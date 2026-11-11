"""Audit sebelum kumpul: bukti freeze (riwayat git), perubahan aturan setelah freeze, secret bocor, file wajib.
Pakai: python audit.py   (exit 1 bila ada GAGAL)"""
import json, re, subprocess, sys, pathlib, datetime as dt
R = pathlib.Path(__file__).parent; bad = []; warn = []
def git(*a):
    r = subprocess.run(["git", "-C", str(R)] + list(a), capture_output=True, text=True); return r.returncode, r.stdout.strip()
def ok(c, m, fatal=True):
    print(("OK    " if c else ("GAGAL " if fatal else "PERIKSA ")) + m)
    if not c: (bad if fatal else warn).append(m)
need = ["README.md", "STRATEGI.md", "public/index.html", "api/status.py", "tests/sim_bot.py", "REFLEKSI.md", "strategy.py", "backtest.py", "api/tick.py", "hitung_ulang.py", "dashboard.html", ".env.example", "FREEZE.txt", "data/log_mentah.json", "data/orders.csv", "data/calls.csv"]
for f in need: ok((R / f).exists(), f"file ada: {f}", fatal=f != "data/orders.csv")
cfg = json.load(open(R / "config.json"))
rc, _ = git("rev-parse", "--git-dir"); ok(rc == 0, "folder .git ada (bukti riwayat commit)")
if rc == 0 and (R / "FREEZE.txt").exists():
    h = (R / "FREEZE.txt").read_text().split()[0]
    rc, full = git("rev-parse", "--verify", h + "^{commit}"); ok(rc == 0, f"commit freeze {h[:10]} ada di riwayat")
    if rc == 0:
        _, cd = git("show", "-s", "--format=%cI", full); t = dt.datetime.fromisoformat(cd)
        ok(t <= dt.datetime.fromisoformat(cfg["fwd_start"]), f"waktu commit freeze {cd} <= {cfg['fwd_start']}")
        _, br = git("branch", "--show-current"); rc2, _ = git("merge-base", "--is-ancestor", full, "HEAD"); ok(rc2 == 0, "commit freeze adalah leluhur HEAD (tidak ditulis ulang)")
        # aturan beku
        _, old = git("show", f"{full}:strategy.py"); ok(old == (R / "strategy.py").read_text().strip(), "strategy.py identik dengan saat freeze")
        _, oc = git("show", f"{full}:config.json")
        try:
            o = json.loads(oc); keys = ["universe", "tf_sec", "capital", "max_positions", "alloc_pct", "daily_loss_limit_pct", "min_order", "fee_buy_pct", "fee_sell_pct", "backtest_spread_pct", "backtest_slip_pct"]
            for k in keys: ok(o.get(k) == cfg.get(k), f"config.{k} sama dgn saat freeze ({cfg.get(k)})")
        except Exception as e: ok(False, f"config.json saat freeze tak terbaca: {e}")
        _, d = git("diff", "--stat", full, "HEAD", "--", "api/", "backtest.py")
        ok(not d, "api/ & backtest.py tidak berubah sejak freeze" + ("" if not d else " -> catat sebagai perbaikan bug di log:\n" + d), fatal=False)
# secret scan pada file terlacak + folder kerja
pat = re.compile(r"(UPSTASH_REDIS_REST_TOKEN[ \t]*=[ \t]*[^\s#]{8,}|CRON_SECRET[ \t]*=[ \t]*[^\s#]{8,}|Bearer\s+[A-Za-z0-9_\-=]{20,}|AX[A-Za-z0-9_=-]{30,})")
leak = []
for p in R.rglob("*"):
    if p.is_file() and ".git" not in p.parts and p.suffix in {".py", ".md", ".json", ".yml", ".txt", ".html", ".csv", ".example", ""} and p.stat().st_size < 3_000_000:
        try: t = p.read_text(errors="ignore")
        except Exception: continue
        for m in pat.finditer(t):
            if "secrets." in t[max(0, m.start() - 20):m.end()] or p.name == "audit.py": continue
            leak.append(f"{p.relative_to(R)}: {m.group(0)[:25]}...")
ok(not leak, "tidak ada secret di file kerja" + ("" if not leak else ": " + "; ".join(leak)))
ok(not (R / ".env").exists(), "tidak ada file .env")
rc, tr = git("ls-files"); ok(rc != 0 or ".env" not in tr.split("\n"), ".env tidak terlacak git")
rc, hist = git("log", "--all", "-p", "-S", "UPSTASH_REDIS_REST_TOKEN=", "--format=%h", "--", ".", ":(exclude)audit.py")
ok(rc != 0 or not re.search(r"UPSTASH_REDIS_REST_TOKEN=[^\s#]{8,}", hist), "tidak ada token di riwayat commit")
ok((R / ".gitignore").exists() and ".env" in (R / ".gitignore").read_text(), ".env ada di .gitignore")
print("\nHASIL:", "LOLOS" if not bad else f"{len(bad)} GAGAL", f"({len(warn)} perlu diperiksa)" if warn else ""); sys.exit(1 if bad else 0)
