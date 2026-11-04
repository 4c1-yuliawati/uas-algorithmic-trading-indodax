# UAS Algorithmic Trading — Indodax Dry-Run Bot

**Student:** Aci Yuliawati  
**NIM:** 25120200012  
**Class:** 3 - Ekonomi Keuangan Profesional  
**Mode:** Simulation only. No Indodax API key and no real orders are used.

> **Status notice (4 Nov 2026):** the lecturer's freeze deadline (4 Nov 2026, 12:00 WIB) has passed. This repository must record the real commit time. Do not backdate a commit or claim that a 10-day forward test has already completed. The scheduled forward window in the assignment is 4 Nov 2026 12:00 WIB to 14 Nov 2026 12:00 WIB. If the bot starts late, record the actual start and ask the lecturer how to handle the missed period. Never manufacture missing logs.

## 1. Strategy inherited from UTS

The supplied AFL file `Trend Following(1).afl` uses EMA 20, EMA 50, EMA 200 and ADX 14 with minimum ADX 20. The crypto adaptation in `src/strategy.ts` preserves the core rules:

- Long-only; no short, margin or leverage.
- Entry signal at the close of a **closed** 4-hour candle when EMA20 crosses above EMA50, close is above EMA200, and ADX(14) > 20.
- Exit signal at the close of a closed 4-hour candle when EMA20 crosses below EMA50.
- The live bot uses the most recent closed candle only; it does not use an unfinished candle.
- Position sizing: maximum 10% of current marked equity per new position; at most 4 open positions.
- Initial virtual capital: Rp100,000,000.
- Daily loss lock: stop opening new positions when marked equity falls 3% below that WIB day's starting equity. Existing positions may still exit.
- No stop-loss or take-profit has been added to the inherited signal rule. Risk is constrained by position count, position sizing and daily loss lock.

The original AFL used daily stock data and `SetTradeDelays(1,1,1,1)`. This project changes the market to Indodax IDR crypto pairs and the timeframe to 4 hours. Signals are calculated only after a candle closes. Live simulated execution is at the current order book, not at candle close or mid-price. All changes must be finalized and committed before the actual forward test begins; this project is currently a late-start preparation and is not evidence of a timely freeze.

## 2. Universe and survivorship-bias control

Candidate pairs are declared in `src/config.ts`: BTC/IDR, ETH/IDR, BNB/IDR, XRP/IDR, ADA/IDR, DOGE/IDR, TRX/IDR and SOL/IDR. This is a **candidate list**, not a claim that all passed liquidity screening. Download 4-hour data for the entire candidate set, then run:

```bash
npm run select-universe
```

The selection script is included as `scripts/select-universe.ts`; run it using `npx tsx scripts/select-universe.ts`. It ranks candidates by median quote turnover (close × base volume) during the first 30 days of the backtest window, requiring at least 150 4-hour bars, and proposes the top six. Inspect `data/universe_selection.json`, confirm the selected set was listed and tradable at the start date using historical pair/listing evidence, then update `CONFIG.candidates` **before** committing the final rules. This avoids choosing only today's winners. If historical listing evidence is unavailable for a pair, exclude it and document the limitation.

## 3. Data and backtest

Public endpoints (no login/API key):

- Candles: `https://indodax.com/tradingview/history_v2?symbol=BTCIDR&tf=240&from=<unix>&to=<unix>`
- Order book: `https://indodax.com/api/depth/btcidr`
- Pair/fee metadata: `https://indodax.com/api/pairs`
- Price increments: `https://indodax.com/api/price_increments`
- Server time: `https://indodax.com/api/server_time`

The downloader paginates backward/forward in sequential requests and waits 400 ms between requests. It saves raw candles to `data/raw/*.csv`. Retrieve at least three full years, preferably 2023-11-04 through the actual freeze/forward start. Record retrieval date/time and file hashes in the final data manifest. Do not treat the existing UTS crypto archive as 4-hour data: its `data/indodax_d1h/*.csv` sample files have date-only rows (daily candles), despite the folder name.

Commands:

```bash
npm install
FROM_DATE=2023-11-04T00:00:00Z TO_DATE=2026-11-04T00:00:00Z npm run download
npm run select-universe
npm run snapshots
npm run manifest
```

Collect order-book snapshots from the beginning of preparation and during forward testing, ideally hourly and at least three times per day. Raw snapshots should be retained. `scripts/backtest.ts` requires `logs/orderbook_snapshots.jsonl` and fails if there are no measured spread/slippage snapshots collected by the forward-test start. It uses median spread and median representative-order slippage measured from those snapshots (representative order notional Rp10,000,000). Set `TAKER_FEE_RATE` to the **more conservative** (higher) taker all-in fee after checking both `/api/pairs` and the official Indodax fee page; record both values, URLs and access timestamps in `docs/fee-audit.md`. Set `MIN_TAKER_FEE_RATE` to the official-page value for the live bot. `BACKTEST_SPREAD_CUTOFF` must be set to the actual forward-test start so later forward snapshots are not leaked into the backtest cost model. The bot obtains the taker rate from `/api/pairs` and takes the maximum of that API rate and `MIN_TAKER_FEE_RATE` (the official documented all-in fee as a decimal). Set `MIN_TAKER_FEE_RATE` after completing `docs/fee-audit.md`. If this is blank/zero, it does not prove the API fee is conservative; do not begin the formal forward test until the fee audit is complete.

Backtest execution uses next 4-hour bar open adjusted by half the measured median spread plus median measured order-book slippage for a representative Rp10,000,000 order. This is an OHLCV approximation; it cannot reproduce historical order-book depth. Forward simulation uses live bid/ask depth and VWAP across levels. Explain this model difference in the final reflection. Minimum order is conservatively Rp25,000. Quantity is simulated in fractional base units; the current code rounds quantity down to 8 decimals as a conservative provisional rule; confirm pair-specific quantity precision and price increments from `/api/price_increments` and pair metadata before using the bot. If the exchange requires a different quantity precision, update and test it before the actual forward start.

Run:

```bash
TAKER_FEE_RATE=YOUR_VERIFIED_DECIMAL MIN_TAKER_FEE_RATE=YOUR_OFFICIAL_DECIMAL BACKTEST_SPREAD_CUTOFF=YOUR_FORWARD_START_ISO npm run backtest
```

**Important:** Replace the placeholder values with verified decimals and an actual timestamp. No fee value is assumed in code. Backtest must not be presented as valid until fee, spread snapshots, slippage, selected universe and 3-year coverage are verified.

## 4. Vercel deployment and scheduling

1. Push this repository to GitHub.
2. Import the repository into Vercel and deploy.
3. Create an Upstash Redis database (Vercel Marketplace or Upstash directly).
4. Add `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, and a long random `CRON_SECRET` in Vercel Environment Variables.
5. Add GitHub Actions repository secrets `BOT_URL` (e.g. `https://your-project.vercel.app`) and `CRON_SECRET` (same value).
6. Enable GitHub Actions. `.github/workflows/hourly-tick.yml` calls `/api/tick` at minute 7 every 4 hours (UTC). The Vercel Hobby cron is daily-only, so this project uses GitHub Actions as the external scheduler.
7. Confirm a successful API connection and persisted logs before counting any forward-test period.

`POST /api/tick` requires `Authorization: Bearer $CRON_SECRET`. The bot uses Upstash Redis for persistent state and raw event logs. To activate the kill switch without redeploying, set Redis key `bot:kill_switch` to string `1`; delete the key or set it to an empty value to deactivate. Each activation is logged. Never place secrets in source files or commit `.env`.

## 5. Logs and reproducibility

Redis list `bot:logs` stores tick calls, simulated orders, order-book snapshots, errors and kill-switch events. Export it from `GET /api/dashboard` and save the response as `logs/forward_logs.json` at submission. Keep the unmodified raw export. The offline dashboard is `public/dashboard.html`; open it locally and import the exported JSON. The live dashboard is `/dashboard.html` on Vercel.

For a same-window comparison, rerun the same backtest engine with `FROM_DATE` and `TO_DATE` set to the actual forward period, and copy `logs/backtest_result.json` to `logs/backtest_same_window.json`. Run `npx tsx scripts/hitung_ulang.ts logs/forward_logs.json logs/backtest_same_window.json` to recalculate core forward metrics and signal-by-signal match rate against the backtest output. Save the exact output and verify it matches the dashboard. A complete final implementation should additionally include the same-window backtest and BTC/IDR buy-and-hold benchmark outputs, and the exact scheduled-candle denominator used for uptime. Do not interpret the dashboard's indicative uptime as the final rubric uptime without that denominator.

## 6. Risk, data validation and operational behavior

- Closed candle only; last closed candle must be no older than 2× timeframe.
- Reject missing candles, zero/non-finite OHLCV, empty order book, invalid bid/ask, and spread >2%; record the reason.
- Orders buy at ask and sell at bid; depth is consumed across levels to calculate VWAP. No fill at mid or close.
- Maximum 4 positions; maximum 10% equity each; daily loss lock 3% at WIB day boundary.
- Idempotency key is the last processed candle timestamp per pair.
- Retry is bounded; request timeout is bounded; all API errors are logged.
- Manual kill switch uses persistent Redis key `bot:kill_switch`.

Before final submission, add pair-specific price/quantity precision checks and validate minimum order/fee details against the current public pair metadata. These must be tested, not merely described.

## 7. Freeze and commit evidence

The assignment requires a public GitHub repository with full commit history or a ZIP containing the complete `.git` directory. Do not force-push after freeze. The freeze deadline in the assignment is 4 Nov 2026 at 12:00 WIB; this project was prepared after that deadline. Commit the current actual state with your own GitHub account and record the real hash and timestamp below. Do not backdate it or claim a pre-deadline freeze.

- Actual commit hash: `FILL AFTER COMMIT`
- Actual commit timestamp (WIB): `FILL AFTER COMMIT`
- Public repository URL: `FILL AFTER PUSH`
- Actual bot first successful run: `FILL FROM LOG`
- Actual forward-test start/end: `FILL FROM LOG`

## 8. Submission checklist

- [ ] Source code and README
- [ ] Strategy rules and UTS change log
- [ ] 3-year+ original Indodax 4h candle data and retrieval manifest
- [ ] Measured raw order-book snapshots and fee audit
- [ ] Backtest result and same-window backtest result
- [ ] Actual forward raw logs (ticks, orders, equity marks, errors, snapshots)
- [ ] `hitung_ulang` output matches dashboard
- [ ] BTC/IDR buy-and-hold benchmark on same period
- [ ] Offline HTML dashboard and live Vercel URL
- [ ] Reflection with numeric explanation of differences
- [ ] `.env.example`; no `.env`, API key or secret
- [ ] Public GitHub link with full commit history; no force push

## 9. Reflection template (complete only after forward test)

1. Actual forward test period and number of scheduled/processed 4h candles.
2. Uptime = processed on-time candles / scheduled candles.
3. Backtest vs forward return and drawdown on the exact same 10-day window.
4. Signal-by-signal match rate and any missed/late candles.
5. Fill-price difference per trade explained by spread, depth/VWAP, slippage and scheduler delay.
6. Fees, spread and slippage as a share of gross profit.
7. API errors, retries, kill-switch events and data-validation rejections.
8. Limitations, including short sample size and OHLCV backtest execution approximation.

Do not fill this section with hypothetical outcomes. Use exported logs and recalculated outputs only.
