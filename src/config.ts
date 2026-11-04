/** Frozen project configuration. Record the actual Git commit/time in README after user commits. */
export const CONFIG = {
  strategyVersion: 'UTS-TrendFollowing-adapted-v1',
  timeframeMinutes: 240,
  timeframeApi: '240',
  timeframeMs: 240 * 60 * 1000,
  // Candidate universe selected for long history; liquidity ranking must be recalculated
  // from quote turnover in the initial backtest window before the freeze commit.
  candidates: ['btcidr','ethidr','bnbidr','xrpidr','adaidr','dogeidr','trxidr','solidr'],
  // Provisional candidate list, not a claim that every pair passed the historical liquidity test.
  initialEquityIdr: 100_000_000,
  maxOpenPositions: 4,
  maxPositionPct: 0.10,
  dailyLossLimitPct: 0.03,
  maxSpreadPct: 0.02,
  maxSlippagePct: 0.001,
  emaFast: 20,
  emaSlow: 50,
  emaTrend: 200,
  adxPeriod: 14,
  minAdx: 20,
  minOrderIdr: 25_000,
  quantityDecimals: 8,
  historyBars: 260,
  retryCount: 2,
  requestTimeoutMs: 12_000,
  // Exchange taker fee is loaded from public /api/pairs at runtime; use max of API field
  // and documented official fee after verifying/citing the official fee page in README.
} as const;

export const INDO = {
  history: 'https://indodax.com/tradingview/history_v2',
  depth: 'https://indodax.com/api/depth/',
  tickerAll: 'https://indodax.com/api/ticker_all',
  pairs: 'https://indodax.com/api/pairs',
  increments: 'https://indodax.com/api/price_increments',
  serverTime: 'https://indodax.com/api/server_time'
};
