"""Rakit ZIP pengumpulan (menyertakan folder .git utuh = bukti freeze). Menolak bila audit GAGAL (kecuali --force)."""
import sys, subprocess, zipfile, pathlib
R = pathlib.Path(__file__).parent; name = (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "UAS_25120200012_AciYuliawati")
if "--force" not in sys.argv and subprocess.run([sys.executable, str(R / "audit.py")]).returncode: sys.exit("Audit GAGAL — perbaiki dulu (atau --force, tidak disarankan).")
skip = {".env", ".vercel", "__pycache__", "node_modules"}; out = R.parent / f"{name}.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(R.rglob("*")):
        if p.is_file() and not (set(p.parts) & skip) and not p.name.endswith(".pyc") and not (p.name.startswith(".env") and p.name != ".env.example"):
            z.write(p, f"{name}/{p.relative_to(R)}")
print("ZIP:", out, f"{out.stat().st_size/1e6:.1f} MB")
