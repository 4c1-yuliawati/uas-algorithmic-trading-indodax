import fs from 'node:fs'; import path from 'node:path';
import { CONFIG,INDO } from '../src/config'; import { normalizeCandles } from '../src/indodax';
const start=Date.parse(process.env.FROM_DATE??'2023-09-22T00:00:00Z'); const end=Date.parse(process.env.TO_DATE??new Date().toISOString());
const pairs=process.env.PAIRS?.split(',').map(x=>x.trim().toLowerCase())??[...CONFIG.candidates];
const outDir=path.resolve('data/raw');fs.mkdirSync(outDir,{recursive:true});
const wait=(ms:number)=>new Promise(r=>setTimeout(r,ms));
async function fetchChunk(pair:string,from:number,to:number){const u=`${INDO.history}?symbol=${pair}&tf=240&from=${Math.floor(from/1000)}&to=${Math.floor(to/1000)}`;const r=await fetch(u,{headers:{'user-agent':'UAS-Indodax-HistoryDownloader/1.0'}});if(!r.ok)throw new Error(`${pair} HTTP ${r.status}`);return normalizeCandles(await r.json());}
async function main(){
  for(const pair of pairs){let cursor=end,all=new Map<number,any>(),iterations=0;
    while(cursor>start&&iterations++<100){const rows=await fetchChunk(pair,start,cursor);if(!rows.length)break;for(const c of rows)if(c.t>=start&&c.t<=end)all.set(c.t,c);
      const earliest=Math.min(...rows.map(x=>x.t));if(earliest>=cursor||earliest<=start)break;cursor=earliest-1;await wait(400);
    }
    const rows=[...all.values()].sort((a,b)=>a.t-b.t);if(!rows.length){console.error(`${pair}: NO_DATA`);continue;}
    const file=path.join(outDir,`${pair}.csv`);fs.writeFileSync(file,'timestamp,open,high,low,close,volume\n'+rows.map(c=>[c.t,c.o,c.h,c.l,c.c,c.v].join(',')).join('\n')+'\n');
    console.log(`${pair}: ${rows.length} bars ${new Date(rows[0].t).toISOString()} - ${new Date(rows.at(-1)!.t).toISOString()}`);
  }
}
main().catch(e=>{console.error(e);process.exit(1)});
