"""Buat DRAF REFLEKSI.md dari angka.json (semua angka dari log; tidak ada yang diketik manual).
Baca, cek, dan sesuaikan kalimatnya dengan pengalaman nyata bot-mu sebelum dikumpulkan."""
import json, pathlib
R = pathlib.Path(__file__).parent; d = json.load(open(R / "angka.json")); c = d["cfg"]
f = lambda x, n=2: "n/a" if x is None else f"{x:,.{n}f}"
pc = lambda x: "n/a" if x is None else f"{x*100:+.2f}%"
fw, bw, bt, up, sg, sp = d["fw"], d["btw"], d["bt"], d.get("up", {}), d.get("sig", {}), d.get("spr", {})
rf, rb = fw["eq"].get("ret"), bw["eq"].get("ret"); gap = None if rf is None or rb is None else (rf - rb) * 100
L = [f"# Refleksi: backtest vs forward test\n*Draf dihasilkan otomatis dari `angka.json` ({d['generated']}). Semua angka dapat dihitung ulang dengan `python hitung_ulang.py`.*\n",
 "## 1. Hasil", f"- Backtest penuh ({(bt['eq'].get('days') or 0)/365.25:.1f} th): return {pc(bt['eq'].get('ret'))}, CAGR {pc(bt['eq'].get('cagr'))}, MDD {pc(bt['eq'].get('mdd'))}, {bt['tr'].get('n',0)} trade, buy&hold BTC/IDR {pc(bt['bh'].get('ret'))}.",
 f"- Jendela forward, backtest: return {pc(rb)}, MDD {pc(bw['eq'].get('mdd'))}, {bw['tr'].get('n',0)} trade.",
 f"- Forward test: return {pc(rf)}, MDD {pc(fw['eq'].get('mdd'))}, {fw['tr'].get('n',0)} trade; buy&hold BTC/IDR {pc(fw['bh'].get('ret'))}.",
 f"- **Gap forward − backtest: {f(gap)} poin persentase** pada jendela yang sama.\n", "## 2. Kecocokan sinyal"]
if sg.get("n"):
    L.append(f"{sg['n']} pasangan candle×pair dibandingkan; kecocokan {sg['match']*100:.2f}%, selisih {len(sg.get('beda',[]))}.")
    if sg.get("beda"): L.append("Selisih terjadi pada: " + "; ".join(f"{b['pair']}@{b['candle_ts']} (bt={b['signal_bt']}, fw={b['signal_fw']})" for b in sg["beda"][:10]) + ". **Jelaskan penyebabnya di sini (mis. candle tidak valid/INVALID di bot, atau bar terlambat).**")
else: L.append("Log sinyal belum lengkap.")
if bt["eq"].get("ret") is not None and bt["bh"].get("ret") is not None:
    L.insert(5, f"- Pembanding: buy&hold BTC/IDR pada periode backtest {pc(bt['bh']['ret'])} vs strategi {pc(bt['eq']['ret'])} — strategi {'mengalahkan' if bt['eq']['ret'] > bt['bh']['ret'] else 'tidak mengalahkan'} buy&hold; return trend-following biasanya menukar sebagian kenaikan dengan proteksi drawdown (MDD strategi {pc(bt['eq'].get('mdd'))}).")
L += ["\n## 3. Sumber selisih (dalam angka)"]
fl = d.get("fills", {}).get("rows", [])
if fl:
    e = [r["entry_diff_pct"] for r in fl]; L.append(f"- Selisih harga fill entry forward vs backtest: rata-rata {sum(e)/len(e):+.3f}% ({len(e)} trade dipasangkan). Backtest mengisi di *open bar berikutnya* ± (spread/2 + slippage); bot mengisi di bid/ask live segera setelah candle tertutup dengan menghabiskan order book.")
    dl = [r["delay_min"] for r in fl]; L.append(f"- Selisih waktu eksekusi: rata-rata {sum(dl)/len(dl):.1f} menit (bot vs open bar backtest) — pada pasar volatil, jeda ini langsung menjadi selisih harga.")
else: L.append(f"- Trade forward {fw['tr'].get('n',0)} vs backtest {bw['tr'].get('n',0)}: tidak ada pasangan trade untuk dibandingkan fill-nya." + (" Dengan 0 trade, kecocokan dinilai dari log sinyal." if fw['tr'].get('n',0) == 0 else ""))
if sp.get("n"): L.append(f"- Spread: median semua snapshot ({sp['n']} snapshot) = {f(sp['median_all'],3)}% vs asumsi backtest {f(sp.get('assumed_bt'),3)}% (selisih {f(sp['median_all']-(sp.get('assumed_bt') or 0),3)} pp). " + "; ".join(f"{k}: {v:.3f}%" for k, v in sp["per_pair"].items()))
for k, nm in [("fee", "fee"), ("spread", "spread"), ("slip", "slippage")]:
    if fw["tr"].get(k) is not None: L.append(f"- Biaya forward — {nm}: Rp{fw['tr'][k]:,.0f}")
if fw["tr"].get("cost_share") is not None: L.append(f"- Porsi biaya ÷ laba kotor forward: {fw['tr']['cost_share']*100:.1f}% (backtest jendela: {f((bw['tr'].get('cost_share') or 0)*100,1)}%).")
L += ["\n## 4. Stabilitas bot", f"- Uptime: {up.get('ontime','n/a')} dari {up.get('expected','n/a')} candle = {f((up.get('uptime') or 0)*100,1)}%; {up.get('calls','n/a')} panggilan tercatat; keterlambatan median {f(up.get('late_med_min'),1)} mnt, maks {f(up.get('late_max_min'),1)} mnt setelah candle tutup.",
 f"- Error tercatat: {d.get('n_err',0)}; pemakaian kill switch: {len(d.get('kill',[]))}.",
 "- Dampak penjadwal luar (GitHub Actions sering terlambat 5–30 menit): sinyal tetap dari candle tertutup sehingga tidak berubah, tetapi harga fill bergeser sebesar pergerakan harga selama keterlambatan.",
 "\n## 5. Keterbatasan\n- Bias survivorship: universe dipilih dari pair Indodax yang masih ada sekarang (kriteria likuiditas diukur Juli–September 2022, tetapi data pair yang delisting tidak tersedia).\n- 10 hari (~20 candle 12 jam) terlalu pendek untuk kesimpulan statistik; selisih return lebih mencerminkan noise dan biaya daripada edge strategi.\n- Fee: lihat `config.json` (`fee_status`) dan sumber yang dicantumkan di dashboard.\n- Strategi trend-following kalah dari buy&hold BTC pada bull market panjang; return bukan kriteria nilai.\n",
 "## 6. Perbaikan bug selama forward test\n*(isi: daftar perbaikan yang tidak mengubah aturan, beserta hash commit & waktu; tulis \"tidak ada\" bila tidak ada)*\n"]
(R / "REFLEKSI.md").write_text("\n".join(L), encoding="utf-8"); print("REFLEKSI.md dibuat (draf) — periksa & lengkapi bagian 2, 3, 6")
