# Indodax fee audit — complete before final run

The assignment requires the taker all-in fee effective on the test date, with both the public `/api/pairs` field and official fee-page value cited; use the higher value.

| Source | Value | URL | Access timestamp (WIB) |
|---|---:|---|---|
| Public API `trade_fee_percent_taker` | TO VERIFY | https://indodax.com/api/pairs | TO FILL |
| Official transaction-fee page | TO VERIFY | https://help.indodax.com/ (Rincian Biaya Transaksi) | TO FILL |
| Applied backtest/live rate | TO FILL | Higher of the two | TO FILL |

Do not use an example/default fee as if it were verified.

The official help-center article confirms that INDODAX adjusted its all-in fee structure effective 1 October 2026 and states that the exact tax/all-in fee details are visible in the user's Profile & Settings / Transaction Information area. The publicly readable article does not expose a numeric taker rate in its text, so do not infer a numeric fee from it. Record the displayed buy/sell all-in taker values from the account page and compare them with the API field. Accessed 4 November 2026. Reference: https://help.indodax.com/hc/id/articles/4416646599705-Rincian-Biaya-Transaksi-di-INDODAX
