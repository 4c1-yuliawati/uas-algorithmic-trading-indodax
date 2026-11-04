import { CONFIG } from './config';
import { adx, ema } from './indicators';
import type { Candle } from './types';
export type Signal = 'BUY'|'SELL'|'HOLD';
export function calculateSignals(c:Candle[]):{signals:Signal[]; fast:number[]; slow:number[]; trend:number[]; adx:number[]} {
  const close=c.map(x=>x.c), fast=ema(close,CONFIG.emaFast), slow=ema(close,CONFIG.emaSlow), trend=ema(close,CONFIG.emaTrend), strength=adx(c,CONFIG.adxPeriod);
  const signals:Signal[]=Array(c.length).fill('HOLD');
  for(let i=1;i<c.length;i++){
    const crossUp=fast[i-1]<=slow[i-1]&&fast[i]>slow[i];
    const crossDown=fast[i-1]>=slow[i-1]&&fast[i]<slow[i];
    if(crossUp&&c[i].c>trend[i]&&strength[i]>CONFIG.minAdx) signals[i]='BUY';
    else if(crossDown) signals[i]='SELL';
  }
  return {signals,fast,slow,trend,adx:strength};
}
