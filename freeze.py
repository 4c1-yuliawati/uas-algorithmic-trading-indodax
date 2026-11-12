"""FREEZE: tetapkan jendela forward 10 hari, commit semua aturan, catat hash di FREEZE.txt.
Pakai (di repo git yang sudah di-init, setelah fee & spread diisi di config.json):  python freeze.py
Setelah itu: git push (wajib!) lalu JANGAN ubah strategy.py / config.json / universe. Jangan force-push."""
import json, subprocess, sys, pathlib, datetime as dt, math
R = pathlib.Path(__file__).parent; WIB = dt.timezone(dt.timedelta(hours=7))
g = lambda *a: subprocess.run(["git", "-C", str(R)] + list(a), capture_output=True, text=True)
cfg = json.load(open(R / "config.json"))
if cfg.get("taker_fee_pct") is None or "SEMENTARA" in cfg["fee_status"] + cfg["spread_status"]:
    sys.exit("Isi dulu di config.json: taker_fee_pct, fee_buy_pct/fee_sell_pct, fee_sources (url+pct+tanggal akses), dan spread (hapus kata SEMENTARA di fee_status & spread_status).")
if any(s.get("pct") is None or s.get("accessed") in (None, "ISI") for s in cfg["fee_sources"]):
    sys.exit("fee_sources belum lengkap: isi pct & accessed untuk SEMUA sumber (termasuk /api/pairs -> trade_fee_percent_taker), pakai yang lebih mahal.")
if g("rev-parse", "--git-dir").returncode: sys.exit("Belum git init.")
now = dt.datetime.now(WIB); start = (now + dt.timedelta(minutes=10)).replace(minute=0, second=0, microsecond=0) + dt.timedelta(hours=1)
cfg["fwd_start"] = start.isoformat(); cfg["fwd_end"] = (start + dt.timedelta(days=10)).isoformat()
json.dump(cfg, open(R / "config.json", "w"), indent=1, ensure_ascii=False)
TR = "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_01WZLm19eKWCK9kezrVzhUCF"
g("add", "-A"); r = g("commit", "-m", f"FREEZE: aturan, parameter, universe dibekukan; forward {cfg['fwd_start']} s/d {cfg['fwd_end']}", "-m", TR)
if r.returncode: sys.exit("commit gagal: " + r.stdout + r.stderr)
h = g("rev-parse", "HEAD").stdout.strip(); t = g("show", "-s", "--format=%cI", h).stdout.strip()
(R / "FREEZE.txt").write_text(f"{h} {t}\nforward_start {cfg['fwd_start']}\nforward_end {cfg['fwd_end']}\n")
g("add", "FREEZE.txt"); g("commit", "-m", "Catat hash commit freeze (FREEZE.txt)", "-m", TR)
print(f"FREEZE commit {h}\nwaktu {t}\nforward test: {cfg['fwd_start']} -> {cfg['fwd_end']}\nSEKARANG: git push (jangan force-push)")
