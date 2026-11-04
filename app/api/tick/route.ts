import { NextRequest, NextResponse } from 'next/server';
import { CONFIG } from '@/src/config';
import { getCandles,getOrderBook,getServerTimeMs,getTakerFeeRate } from '@/src/indodax';
import { calculateSignals } from '@/src/strategy';
import { fillFromBook,estimateBookSlippage } from '@/src/execution';
import { appendLog,db } from '@/src/store';
import { emptyState,equity,jakartaDay,type BotState } from '@/src/portfolio';
import type { Candle,Position } from '@/src/types';
export const runtime='nodejs'; export const maxDuration=60;
const stateKey='bot:state';
async function safeLog(x:any){await appendLog(x);}
export async function POST(req:NextRequest){
  const started=Date.now(), nowIso=new Date().toISOString();
  if(!process.env.CRON_SECRET||req.headers.get('authorization')!==`Bearer ${process.env.CRON_SECRET}`)return NextResponse.json({ok:false,error:'UNAUTHORIZED'},{status:401});
  let state:BotState=await db().get<BotState>(stateKey)??emptyState();
  try{
    const serverMs=await getServerTimeMs(), day=jakartaDay(serverMs);
    if(await db().get('bot:kill_switch')){await safeLog({type:'kill_switch',timestamp:new Date(serverMs).toISOString(),enabled:true});return NextResponse.json({ok:true,killed:true});}
    const dayChanged=state.dayKey!==day;if(dayChanged){state.dayKey=day;state.dayStartEquity=equity(state,{});state.dailyLocked=false;}
    const feeRate=await getTakerFeeRate(); let processed=0,orders=0,errors=0;
    const bidMarks:Record<string,number>={};
    for(const pair of CONFIG.candidates){
      try{
        const candles=await getCandles(pair,serverMs-CONFIG.timeframeMs*(CONFIG.historyBars+5),serverMs);
        const closed=candles.filter(c=>c.t+CONFIG.timeframeMs<=serverMs);
        if(closed.length<CONFIG.emaTrend+CONFIG.adxPeriod+5)throw new Error('INSUFFICIENT_CLOSED_CANDLES');
        for(let i=1;i<closed.length;i++)if(closed[i].t-closed[i-1].t>CONFIG.timeframeMs*1.5)throw new Error('MISSING_CANDLE_GAP');
        const last=closed[closed.length-1], prev=closed[closed.length-2];
        if(serverMs-last.t>CONFIG.timeframeMs*2)throw new Error('STALE_LAST_CLOSED_CANDLE');
        if([last.o,last.h,last.l,last.c,last.v].some(x=>!Number.isFinite(x)||x<=0))throw new Error('INVALID_OHLCV');
        const book=await getOrderBook(pair), bid=Math.max(...book.buy.map(x=>x.price)), ask=Math.min(...book.sell.map(x=>x.price));
        if(!bid||!ask)throw new Error('ORDER_BOOK_EMPTY');
        const spread=(ask-bid)/((ask+bid)/2);
        bidMarks[pair]=bid;
        let slip:any={slippageUnavailable:true};try{slip=estimateBookSlippage(book,10_000_000);}catch(e){slip={slippageUnavailable:true,slippageError:e instanceof Error?e.message:String(e)};}
        await safeLog({type:'orderbook_snapshot',timestamp:new Date(serverMs).toISOString(),pair,candleTime:last.t,candleClose:last.c,bestBid:bid,bestAsk:ask,spreadPct:spread,...slip,bids:book.buy.slice(0,10),asks:book.sell.slice(0,10)});
        if(spread>CONFIG.maxSpreadPct)throw new Error('SPREAD_OVER_2_PERCENT');
        if(state.lastProcessed[pair]===last.t){continue;}
        await safeLog({type:'market_mark',timestamp:new Date(serverMs).toISOString(),pair,candleTime:last.t,close:last.c,bestBid:bid});
        const {signals}=calculateSignals(closed); const signal=signals[signals.length-1];
        await safeLog({type:'signal',timestamp:new Date(serverMs).toISOString(),pair,candleTime:last.t,signal,close:last.c});
        const existing=state.positions[pair];
        if(signal==='BUY'&&!existing&&!state.dailyLocked&&Object.keys(state.positions).length<CONFIG.maxOpenPositions){
          const eq=equity(state,bidMarks),budget=Math.min(eq*CONFIG.maxPositionPct,state.cash);
          if(budget>=CONFIG.minOrderIdr){let qty=Math.floor((budget/ask)*10**CONFIG.quantityDecimals)/10**CONFIG.quantityDecimals;let fill=fillFromBook(book,'buy',qty);if(fill.notional>budget){qty=qty*budget/fill.notional;fill=fillFromBook(book,'buy',qty);}const fee=fill.notional*feeRate;
            if(fill.notional+fee<=state.cash&&fill.notional<=budget*1.000001){state.cash-=fill.notional+fee;state.positions[pair]={pair,qty,avgEntry:fill.fillAvg,entryFee:fee,openedAt:new Date(serverMs).toISOString(),lastSignalCandle:last.t};
              await safeLog({type:'order',timestamp:new Date(serverMs).toISOString(),candleTime:last.t,pair,side:'buy',qty,bestBid:fill.bestBid,bestAsk:fill.bestAsk,fillAvg:fill.fillAvg,notional:fill.notional,feeRate,fee,signalClose:last.c,slippageVsSignalPct:(fill.fillAvg/last.c-1)*100,levelsConsumed:fill.levelsConsumed});orders++;}
          }
        }else if(signal==='SELL'&&existing){const sellQty=Math.floor(existing.qty*10**CONFIG.quantityDecimals)/10**CONFIG.quantityDecimals;const fill=fillFromBook(book,'sell',sellQty),fee=fill.notional*feeRate;state.cash+=fill.notional-fee;
          await safeLog({type:'order',timestamp:new Date(serverMs).toISOString(),candleTime:last.t,pair,side:'sell',qty:sellQty,bestBid:fill.bestBid,bestAsk:fill.bestAsk,fillAvg:fill.fillAvg,notional:fill.notional,feeRate,fee,signalClose:last.c,slippageVsSignalPct:(last.c/fill.fillAvg-1)*100,levelsConsumed:fill.levelsConsumed,realizedPnl:fill.notional-fee-sellQty*existing.avgEntry-existing.entryFee});delete state.positions[pair];orders++;}
        state.lastProcessed[pair]=last.t;await db().set(stateKey,state);processed++;
      }catch(e){errors++;await safeLog({type:'error',timestamp:new Date().toISOString(),pair,message:e instanceof Error?e.message:String(e)});}
    }
    const eq=equity(state,bidMarks); if(eq<=state.dayStartEquity*(1-CONFIG.dailyLossLimitPct))state.dailyLocked=true;
    await db().set(stateKey,state);
    if(dayChanged)await safeLog({type:'daily_equity',timestamp:new Date(serverMs).toISOString(),dayKey:state.dayKey,equity:eq,dayStartEquity:state.dayStartEquity});
    await safeLog({type:'tick',timestamp:nowIso,serverTime:new Date(serverMs).toISOString(),scheduledSlot:Math.floor((serverMs-7*60_000)/CONFIG.timeframeMs),durationMs:Date.now()-started,processed,orders,errors,equity:eq,cash:state.cash,openPositions:Object.keys(state.positions).length,dailyLocked:state.dailyLocked,dayKey:state.dayKey});
    return NextResponse.json({ok:true,processed,orders,errors,equity:eq,dailyLocked:state.dailyLocked});
  }catch(e){await safeLog({type:'fatal',timestamp:new Date().toISOString(),message:e instanceof Error?e.message:String(e)});return NextResponse.json({ok:false,error:e instanceof Error?e.message:String(e)},{status:500});}
}
