"""Check every bundled logo against the original it replaces.

Usage: python3 tools/lunchbox_logos/verify.py RUNTIME apps/APP

For each URL and size in apps/APP/logos.star this downloads the URL again,
renders the original bytes drawn at that size (what the app did before) and the
bundled bytes in frames of the same animation, and requires byte-identical WebP
output. URLs whose source changed since generation are skipped and counted.
"""
import hashlib, json, re, subprocess, sys, tempfile, urllib.request, urllib.error, concurrent.futures
from pathlib import Path
runtime, appdir = sys.argv[1], Path(sys.argv[2])
src = (appdir / "logos.star").read_text()
symbols = dict((m.group(2), m.group(1)) for m in re.finditer(r'load\("([^"]+)", (\w+) = "file"\)', src))
entries = []
packs = [p for p, _ in sorted(((p, s) for s, p in symbols.items() if "pack-" in p))]
def data(path):
    if isinstance(path, tuple):
        pack, start, end = path
        return (appdir / packs[pack]).read_bytes()[start:end]
    return (appdir / path).read_bytes()
for m in re.finditer(r'    # [^\n]*source sha256 ([0-9a-f]+)\n    "([^"]+)": \{\n((?:        \d+: [^\n]+,\n)+)', src):
    digest, url, body = m.groups()
    for size, sym in re.findall(r'(\d+): (\w+),', body):
        entries.append((url, digest, int(size), symbols[sym]))
    for size, p, a, z in re.findall(r'(\d+): \((\d+), (\d+), (\d+)\)', body):
        entries.append((url, digest, int(size), (int(p), int(a), int(z))))
print(appdir.name, len(entries), "bundled url/size pairs")
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Go-http-client/1.1"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r: return r.read()
        except Exception as e: err = e
    raise err
urls = sorted({e[0] for e in entries})
with concurrent.futures.ThreadPoolExecutor(16) as p:
    originals = dict(zip(urls, p.map(fetch, urls)))
changed = [u for u in urls if hashlib.sha256(originals[u]).hexdigest() != next(e[1] for e in entries if e[0] == u)]
print("sources changed upstream since generation:", len(changed))
def run(batch, idx, tmp):
    outs = []
    for kind in ("orig", "bund"):
        d = tmp / f"{kind}{idx}"; d.mkdir()
        loads, frames = [], []
        for i, (url, _, size, path) in enumerate(batch):
            f = f"f{i}.bin"
            (d / f).write_bytes(originals[url] if kind == "orig" else data(path))
            loads.append(f'load("{f}", F{i} = "file")')
            frames.append(f'render.Box(width = 64, height = 32, color = "#123", child = render.Image(src = F{i}.readall(), width = {size}, height = {size}))')
        (d / "v.star").write_text('load("render.star", "render")\n' + "\n".join(loads) + "\ndef main(config):\n    return render.Root(delay = 10, child = render.Animation(children = [\n        " + ",\n        ".join(frames) + "]))\n")
        out = d / "o.webp"
        subprocess.run([runtime, "render", str(d / "v.star"), "-o", str(out), "--silent", "-z", "0", "-d", "60s"], check=True, capture_output=True, env={"PIXLET_IMAGE_CACHE_DIR": "", "PATH": "/usr/bin:/bin"})
        outs.append(out.read_bytes())
    return outs[0] == outs[1]
ok = bad = 0
todo = [e for e in entries if e[0] not in changed]
with tempfile.TemporaryDirectory() as t:
    t = Path(t); batches = [todo[i:i+250] for i in range(0, len(todo), 250)]
    with concurrent.futures.ThreadPoolExecutor(4) as p:
        for b, same in zip(batches, p.map(lambda a: run(a[1], a[0], t), enumerate(batches))):
            if same: ok += len(b)
            else: bad += len(b); print("DIFFERENT batch starting", b[0][:3])
print(f"{appdir.name}: {ok}/{len(todo)} bundled url/size pairs render identically to the original ({bad} in differing batches)")
sys.exit(1 if bad else 0)
