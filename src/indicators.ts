import type { Candle } from './types';
export function ema(values:number[], period:number): number[] {
  const out:number[] = Array(values.length).fill(NaN); if(values.length < period) return out;
  const k=2/(period+1); let seed=0; for(let i=0;i<period;i++) seed+=values[i];
  out[period-1]=seed/period; for(let i=period;i<values.length;i++) out[i]=values[i]*k+out[i-1]*(1-k); return out;
}
function wilder(values:number[], period:number):number[] {
  const out:number[]=Array(values.length).fill(NaN); if(values.length<=period) return out;
  let s=0; for(let i=1;i<=period;i++) s+=values[i]; out[period]=s/period;
  for(let i=period+1;i<values.length;i++) out[i]=(out[i-1]*(period-1)+values[i])/period; return out;
}
export function adx(c:Candle[], period:number):number[] {
  const tr:number[]=Array(c.length).fill(NaN), plus:number[]=Array(c.length).fill(0), minus:number[]=Array(c.length).fill(0);
  for(let i=1;i<c.length;i++){
    const up=c[i].h-c[i-1].h, down=c[i-1].l-c[i].l;
    plus[i]=up>down&&up>0?up:0; minus[i]=down>up&&down>0?down:0;
    tr[i]=Math.max(c[i].h-c[i].l,Math.abs(c[i].h-c[i-1].c),Math.abs(c[i].l-c[i-1].c));
  }
  const atr=wilder(tr.map(x=>Number.isFinite(x)?x:0),period), p=wilder(plus,period), m=wilder(minus,period);
  const dx:number[]=Array(c.length).fill(NaN);
  for(let i=0;i<c.length;i++){ if(atr[i]>0){const pdi=100*p[i]/atr[i],mdi=100*m[i]/atr[i]; dx[i]=pdi+mdi===0?0:100*Math.abs(pdi-mdi)/(pdi+mdi);} }
  return wilder(dx.map(x=>Number.isFinite(x)?x:0),period);
}
