import { CONFIG, INDO } from './config';
import type { BookLevel, Candle, OrderBook } from './types';
const sleep=(ms:number)=>new Promise(r=>setTimeout(r,ms));
async function getJson(url:string):Promise<any>{
  let last:any; for(let i=0;i<=CONFIG.retryCount;i++){
    const ctrl=new AbortController(), timer=setTimeout(()=>ctrl.abort(),CONFIG.requestTimeoutMs);
    try{const r=await fetch(url,{signal:ctrl.signal,headers:{'accept':'application/json','user-agent':'UAS-Indodax-DryRun/1.0'}}); if(!r.ok) throw new Error(`HTTP_${r.status}`); return await r.json();}
    catch(e){last=e;if(i<CONFIG.retryCount) await sleep(500*(i+1));} finally{clearTimeout(timer);}
  } throw last;
}
export async function getServerTimeMs():Promise<number>{const j=await getJson(INDO.serverTime); const v=Number(j.server_time??j.serverTime??j); return v<1e12?v*1000:v;}
export function normalizeCandles(raw:any):Candle[]{
  let rows=Array.isArray(raw)?raw:(raw?.data??raw?.result??[]);
  if(Array.isArray(raw?.t)){rows=raw.t.map((t:number,i:number)=>({t,o:raw.o?.[i],h:raw.h?.[i],l:raw.l?.[i],c:raw.c?.[i],v:raw.v?.[i]}));}
  return rows.map((x:any)=>({t:Number(x.t??x.time??x[0])*((Number(x.t??x.time??x[0])<1e12)?1000:1),o:Number(x.o??x.open??x[1]),h:Number(x.h??x.high??x[2]),l:Number(x.l??x.low??x[3]),c:Number(x.c??x.close??x[4]),v:Number(x.v??x.volume??x[5])})).filter((x:Candle)=>[x.t,x.o,x.h,x.l,x.c,x.v].every(Number.isFinite)).sort((a:Candle,b:Candle)=>a.t-b.t);
}
export async function getCandles(pair:string,from:number,to:number):Promise<Candle[]>{
  const url=`${INDO.history}?symbol=${encodeURIComponent(pair)}&tf=${CONFIG.timeframeApi}&from=${Math.floor(from/1000)}&to=${Math.floor(to/1000)}`;
  return normalizeCandles(await getJson(url));
}
function levels(raw:any):BookLevel[]{return (raw??[]).map((x:any)=>({price:Number(Array.isArray(x)?x[0]:x.price),vol:Number(Array.isArray(x)?x[1]:x.vol)})).filter((x:BookLevel)=>x.price>0&&x.vol>0);}
export async function getOrderBook(pair:string):Promise<OrderBook>{const j=await getJson(`${INDO.depth}${pair}`);return {buy:levels(j.buy??j.bids),sell:levels(j.sell??j.asks)};}
export async function getTakerFeeRate():Promise<number>{
  const j=await getJson(INDO.pairs); const rows=Array.isArray(j)?j:Object.values(j?.pairs??j??{});
  const vals=rows.map((x:any)=>Number(x.trade_fee_percent_taker)).filter((x:number)=>Number.isFinite(x)&&x>=0);
  if(!vals.length) throw new Error('TAKER_FEE_NOT_FOUND_IN_PUBLIC_PAIRS');
  // Conservative: highest published taker fee among candidate pairs.
  const apiRate=Math.max(...vals)/100;if(!process.env.MIN_TAKER_FEE_RATE)throw new Error('MIN_TAKER_FEE_RATE_REQUIRED_COMPLETE_FEE_AUDIT');const documented=Number(process.env.MIN_TAKER_FEE_RATE);if(!Number.isFinite(documented)||documented<=0)throw new Error('INVALID_MIN_TAKER_FEE_RATE');return Math.max(apiRate,documented);
}
export async function getPriceIncrement(pair:string):Promise<number>{
  const j=await getJson(INDO.increments); const v=Number(j?.[pair]?.price_increment??j?.[pair]??1); return Number.isFinite(v)&&v>0?v:1;
}
