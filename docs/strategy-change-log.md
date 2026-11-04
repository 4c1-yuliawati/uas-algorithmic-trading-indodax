# Catatan perubahan strategi dari UTS

1. Pasar saham Indonesia/Kompas 100 diganti menjadi pasangan kripto IDR Indodax.
2. Timeframe disesuaikan menjadi 4 jam agar tersedia lebih banyak observasi selama forward test 10 hari.
3. Sinyal inti UTS dipertahankan: EMA cepat 20, EMA lambat 50, EMA tren 200, ADX 14, ambang ADX 20.
4. Aturan entry: EMA20 cross-up EMA50, close di atas EMA200, ADX14 > 20.
5. Aturan exit: EMA20 cross-down EMA50.
6. Eksekusi backtest: bar berikutnya; forward: order book live, buy ask dan sell bid dengan VWAP level.
7. Risk controls untuk bot: modal virtual Rp100 juta, maksimum 4 posisi, maksimum 10% equity per posisi, daily loss lock 3% WIB, kill switch dan idempotency.
8. Penyesuaian pasar, universe dan parameter harus tercatat dalam commit yang benar-benar dibuat sebelum forward run; jadwal freeze tugas telah terlewati sehingga commit terlambat tidak boleh disebut sebagai freeze tepat waktu.
