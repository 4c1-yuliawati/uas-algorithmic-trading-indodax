import type { OrderBook, Side } from './types';
export function fillFromBook(book:OrderBook,side:Side,qty:number){
  const rows=[...(side==='buy'?book.sell:book.buy)].sort((a,b)=>side==='buy'?a.price-b.price:b.price-a.price);
  if(!rows.length) throw new Error('ORDER_BOOK_EMPTY');
  const bestBid=Math.max(...book.buy.map(x=>x.price)),bestAsk=Math.min(...book.sell.map(x=>x.price));
  if(!bestBid||!bestAsk||bestAsk<bestBid) throw new Error('ORDER_BOOK_INVALID');
  const spreadPct=(bestAsk-bestBid)/((bestAsk+bestBid)/2); if(spreadPct>0.02) throw new Error(`SPREAD_TOO_WIDE_${(spreadPct*100).toFixed(4)}pct`);
  let remaining=qty,notional=0,filled=0,levelsConsumed=0;
  for(const level of rows){if(remaining<=0)break;const take=Math.min(remaining,level.vol);notional+=take*level.price;filled+=take;remaining-=take;levelsConsumed++;}
  if(remaining>Math.max(1e-10,qty*1e-8)) throw new Error('INSUFFICIENT_ORDER_BOOK_DEPTH');
  return {bestBid,bestAsk,fillAvg:notional/filled,notional,levelsConsumed,spreadPct};
}

export function estimateBookSlippage(book:OrderBook,notionalIdr:number){
  const bestAsk=Math.min(...book.sell.map(x=>x.price)),bestBid=Math.max(...book.buy.map(x=>x.price));
  const buyQty=notionalIdr/bestAsk,sellQty=notionalIdr/bestBid;
  const buy=fillFromBook(book,'buy',buyQty),sell=fillFromBook(book,'sell',sellQty);
  return {buySlippagePct:(buy.fillAvg/bestAsk-1)*100,sellSlippagePct:(1-sell.fillAvg/bestBid)*100,representativeNotionalIdr:notionalIdr};
}
