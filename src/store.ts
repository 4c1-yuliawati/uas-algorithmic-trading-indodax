import { Redis } from '@upstash/redis';
let redis:Redis|undefined;
export function db(){if(!process.env.UPSTASH_REDIS_REST_URL||!process.env.UPSTASH_REDIS_REST_TOKEN)throw new Error('UPSTASH_REDIS_ENV_MISSING');return redis??=(new Redis({url:process.env.UPSTASH_REDIS_REST_URL,token:process.env.UPSTASH_REDIS_REST_TOKEN}));}
export async function appendLog(event:any){await db().lpush('bot:logs',JSON.stringify(event));}
export async function readLogs(limit=5000){const rows=await db().lrange<string>('bot:logs',0,limit-1);return rows.map(x=>typeof x==='string'?JSON.parse(x):x).reverse();}
