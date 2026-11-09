
import { Redis } from '@upstash/redis';

let redis: Redis | undefined;

export function db() {
  const url = (
    process.env.UPSTASH_REDIS_REST_URL ||
    process.env.UPSTASH_REDIS_REST_KV_REST_API_URL
  )?.trim();

  const token = (
    process.env.UPSTASH_REDIS_REST_TOKEN ||
    process.env.UPSTASH_REDIS_REST_KV_REST_API_TOKEN
  )?.trim();

  if (!url || !token) {
    throw new Error('UPSTASH_REDIS_ENV_MISSING');
  }

  return (
    redis ??
    (redis = new Redis({
      url,
      token,
    }))
  );
}

export async function appendLog(event: any) {
  await db().lpush('bot:logs', JSON.stringify(event));
}

export async function readLogs(limit = 5000) {
  const rows = await db().lrange<string>('bot:logs', 0, limit - 1);
  return rows.map((x) => (typeof x === 'string' ? JSON.parse(x) : x)).reverse();
}
