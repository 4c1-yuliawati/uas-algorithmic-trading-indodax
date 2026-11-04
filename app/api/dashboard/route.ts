import { NextResponse } from 'next/server';
import { readLogs } from '@/src/store';
export const runtime='nodejs';
export async function GET(){try{return NextResponse.json({generatedAt:new Date().toISOString(),logs:await readLogs(10000)});}catch(e){return NextResponse.json({error:e instanceof Error?e.message:String(e),logs:[]},{status:503});}}
