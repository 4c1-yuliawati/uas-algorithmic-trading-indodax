export type Candle = { t:number; o:number; h:number; l:number; c:number; v:number };
export type BookLevel = { price:number; vol:number };
export type OrderBook = { buy:BookLevel[]; sell:BookLevel[] };
export type Side = 'buy'|'sell';
export type Position = { pair:string; qty:number; avgEntry:number; entryFee:number; openedAt:string; lastSignalCandle:number };
export type SimOrder = { type:'order'; timestamp:string; candleTime:number; pair:string; side:Side; qty:number; bestBid:number; bestAsk:number; fillAvg:number; notional:number; feeRate:number; fee:number; signalClose:number; slippageVsSignalPct:number; levelsConsumed:number };
