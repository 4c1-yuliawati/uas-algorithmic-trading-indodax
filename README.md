# UAS Algoritma Trading — Bot Dry Run Indodax (Trend Following 12 jam)
Bot **dry run**: order simulasi, tanpa uang, tanpa API key Indodax. Hanya API publik Indodax.

## Isi repo
| Berkas | Fungsi |
|---|---|
| `strategy.py` | fungsi sinyal — **dipakai sama** oleh `backtest.py` dan `api/tick.py` |
| `backtest.py` | backtest 4 tahun (data asli Indodax di `data_hist/`), fee + spread + slippage |
| `api/tick.py` | bot (dipanggil penjadwal): data live → sinyal → order simulasi → state & log di Redis |
| `api/export.py`, `api/kill.py`, `api/status.py` | ekspor log (rahasia), kill switch (rahasia), status publik untuk dashboard |
| `public/index.html` | dashboard live di Vercel (membaca `/api/status`) |
| `export_logs.py` → `hitung_ulang.py` | tarik log mentah → hitung ulang SEMUA angka → `dashboard.html` offline + `angka.json` |
| `make_refleksi.py` | draf `REFLEKSI.md` dari `angka.json` |
| `update_hist.py` | (laptop) perbarui data historis s/d akhir forward untuk backtest jendela yang sama |
| `freeze.py`, `audit.py`, `build_zip.py` | freeze + commit, audit pra-kumpul, rakit ZIP |
| `tests/sim_bot.py` | uji offline: sinyal bot = backtest, idempotency, fill di bid/ask |
| `.github/workflows/tick.yml` | penjadwal tiap jam menit ke-7 |

## Langkah (urut)
1. **Repo baru** di GitHub (publik). `git init`, hubungkan remote, push awal. Jangan pernah commit `.env`.
2. **Upstash Redis** (Vercel → Storage/Marketplace). Catat `UPSTASH_REDIS_REST_URL` dan `..._TOKEN`.
3. **Vercel**: import repo → Environment Variables: `CRON_SECRET` (acak ≥32 karakter), `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, `KILL_SWITCH=0` → Deploy.
4. **GitHub → Settings → Secrets → Actions**: `CRON_SECRET` (sama), `BOT_URL` (mis. `https://nama-app.vercel.app`).
5. **Uji koneksi** (wajib sebelum freeze): `curl -H "Authorization: Bearer $CRON_SECRET" $BOT_URL/api/tick`. Lalu `python export_logs.py` dan lihat ringkasan: tidak boleh ada error `DEPTH`/`SERVER_TIME`, dan `signals` terisi (membuktikan format `history_v2` terbaca). Jika Indodax tak bisa diakses dari Vercel → lapor dosen sebelum freeze.
6. **Fee & spread**: isi `config.json` dari halaman resmi + `/api/pairs` (pakai yang lebih mahal; catat URL & tanggal akses). Spread/slippage: median snapshot (`data/snapshots.csv` setelah `export_logs.py`). Hapus kata "SEMENTARA" pada `fee_status` dan `spread_status`. Jalankan ulang `python backtest.py`.
7. **Bersihkan state uji**: sebelum freeze kosongkan Redis (Upstash console → `FLUSHDB`) agar forward test mulai dari modal Rp100.000.000. Snapshot yang dipakai untuk spread sudah Anda ekspor di langkah 6 (simpan sebagai `data_hist/snapshots_prefreeze.csv`).
8. **Freeze**: `python freeze.py` (menetapkan 10 hari forward dari jam berikutnya, commit, tulis `FREEZE.txt`) → `git push`. Jangan ubah `strategy.py`/`config.json`/universe sesudahnya; perbaikan bug non-aturan boleh tetapi catat di `REFLEKSI.md`.
9. **Selama forward**: pantau `public/index.html` di Vercel. Kill switch: `curl -H "Authorization: Bearer $CRON_SECRET" "$BOT_URL/api/kill?on=1"` (`on=0` untuk mati).
10. **Setelah forward berakhir** (laptop): `python update_hist.py` (tarik data s/d akhir forward) → `python backtest.py --window` → `BOT_URL=... CRON_SECRET=... python export_logs.py` → `python hitung_ulang.py` → `python make_refleksi.py` → baca & lengkapi `REFLEKSI.md` (bagian 2, 3, 6).
11. **Kumpul**: `python audit.py` (harus LOLOS) → `python build_zip.py` → unggah ZIP di RISE; tulis link Vercel dan link repo di kolom catatan.

## Uji offline (tanpa internet)
`python tests/sim_bot.py` — Redis & Indodax tiruan; membuktikan sinyal bot identik dengan backtest candle demi candle, panggilan ganda tidak membeli dua kali, fill di bid/ask.

## Catatan jujur
- Spread/slippage backtest sebelum freeze = ukuran snapshot yang terkumpul; bandingkan dengan seluruh snapshot di refleksi.
- Penjadwal GitHub Actions bisa terlambat; sinyal tetap dari candle tertutup, harga fill bergeser — dibahas di refleksi dan diukur lewat `calls.csv`.
- Strategi bukan nasihat investasi; hasil backtest tidak menjamin hasil forward.
