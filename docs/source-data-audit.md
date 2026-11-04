# Audit file data UTS yang tersedia

File `onaldhi_data_pasar(1).zip` memiliki folder `data/indodax_d1h/`, tetapi sampel CSV yang diperiksa menggunakan kolom `t,o,h,l,c,v` dengan timestamp tanggal harian, bukan timestamp 4-jam. Contoh rentang yang diperiksa:

| Pair | Bar | Tanggal awal | Tanggal akhir |
|---|---:|---|---|
| BTC/IDR | 3,046 | 2018-05-31 | 2026-10-01 |
| ETH/IDR | 2,849 | 2018-12-14 | 2026-10-01 |
| BNB/IDR | 2,593 | 2019-08-27 | 2026-10-01 |
| SOL/IDR | 1,590 | 2022-05-26 | 2026-10-01 |
| XRP/IDR | 2,856 | 2018-12-14 | 2026-10-08 |
| ADA/IDR | 2,849 | 2018-12-14 | 2026-10-01 |
| DOGE/IDR | 2,802 | 2019-02-06 | 2026-10-08 |
| TRX/IDR | 2,852 | 2018-12-18 | 2026-10-08 |

Kesimpulan: data ini berguna sebagai referensi daily, tetapi **tidak dipakai sebagai pengganti candle 4h** dalam backtest UAS. Script `download-history.ts` mengambil candle tf=240 langsung dari public history API Indodax. Data 4h yang benar harus diunduh dan disertakan bersama paket final.
