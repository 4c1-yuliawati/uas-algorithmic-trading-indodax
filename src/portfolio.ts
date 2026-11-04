import { CONFIG } from './config';
import type { Position } from './types';
export type BotState={cash:number;positions:Record<string,Position>;lastProcessed:Record<string,number>;dayKey:string;dayStartEquity:number;dailyLocked:boolean};
export function emptyState():BotState{return {cash:CONFIG.initialEquityIdr,positions:{},lastProcessed:{},dayKey:'',dayStartEquity:CONFIG.initialEquityIdr,dailyLocked:false};}
export function equity(state:BotState,bids:Record<string,number>):number{return state.cash+Object.values(state.positions).reduce((s,p)=>s+p.qty*(bids[p.pair]??p.avgEntry),0);}
export function jakartaDay(ms:number):string{return new Date(ms+7*3600_000).toISOString().slice(0,10);}
