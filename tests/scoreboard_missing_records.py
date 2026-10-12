"""Offline renders of recorded ESPN events that crashed earlier score apps.

python3 tests/scoreboard_missing_records.py ../niblet-cli/niblet

tests/scoreboard_missing_records.json holds real scoreboard events in which one
competitor has no "records" (preseason and exhibition opponents, Division
II/III and NCAA soccer opponents, a cup match shown as postponed) and soccer
penalty-shootout finals. Every layout must render them with the record line.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
runtime = str(Path(sys.argv[1]).resolve())
fixtures = json.loads((root / "tests/scoreboard_missing_records.json").read_text())

LAYOUTS = {
    "nbascores": ["colors", "black", "logos", "horizontal", "stadium", "retro"],
    "wnbascores": ["colors", "black", "logos", "horizontal", "stadium", "retro"],
    "ncaafscores": ["colors", "black", "logos", "horizontal", "stadium", "retro"],
    "soccermens": ["colors", "black", "horizontal", "retro", "wide3", "wide4"],
    "soccerwomens": ["colors", "black", "horizontal", "retro", "wide3", "wide4"],
}

overrides = '''
load("pixel.png", TEST_LOGO = "file")
FIXTURE_EVENTS = json.decode(%s)
def get_logoType(*args, **kwargs):
    return TEST_LOGO.readall()
def get_cachable_data(url, ttl_seconds = 60):
    if "/scoreboard" not in url:
        return TEST_LOGO.readall()
    return json.encode({"events": FIXTURE_EVENTS})
'''

checked = 0
apps = [app for app in LAYOUTS if app in fixtures]
for app in apps:
    layouts = LAYOUTS[app]
    events = fixtures[app]["events"]
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        source = next(p for p in (root / "apps" / app).glob("*.star") if p.name != "logos.star").read_text()
        for name in ("images", "logos"):
            if (root / "apps" / app / name).exists():
                shutil.copytree(root / "apps" / app / name, tmp / name)
        # logos.star holds bundled logos; the manifest enables 2x (Wide layouts).
        for name in ("logos.star", "manifest.yaml"):
            if (root / "apps" / app / name).exists():
                shutil.copy(root / "apps" / app / name, tmp / name)
        (tmp / "pixel.png").write_bytes((root / "apps/nhlnextgame/images/ana.png").read_bytes())
        source = source.replace("def get_cachable_data(", "def original_get_cachable_data(", 1)
        source = source.replace("def get_logoType(", "def original_get_logoType(", 1)
        if app in ("soccermens", "soccerwomens"):
            # Competition labels and options are external metadata.
            source = source.replace("json.decode(http.get(url = ABBR_URL, ttl_seconds = COMPS_TTL).body())", "{DEFAULT_LEAGUE: \"TEST\"}")
            source = source.replace("def get_schema(", "def original_get_schema(", 1)
        source += overrides % repr(json.dumps(events))
        (tmp / "scores.star").write_text(source)
        for layout in layouts:
            for scale in ([2] if layout.startswith("wide") else [1]):
                args = [runtime, "render", str(tmp / "scores.star"), "displayType=" + layout, "pregameDisplay=record",
                        "rotationSpeed=1", "displaySpeed=1000", "--now", "2026-10-12T18:00:00Z",
                        "--output", str(tmp / "out.webp"), "--metadata-output", str(tmp / "meta.json"),
                        "--timeout", "20s", "--silent"] + (["-2"] if scale == 2 else [])
                result = subprocess.run(args, capture_output=True, text=True)
                assert result.returncode == 0, (app, layout, scale, result.stderr[-800:])
                frames = json.loads((tmp / "meta.json").read_text())["frame_count"]
                # One card per game, except the paged wide soccer layouts.
                assert frames == len(events) or (layout.startswith("wide") and frames > 0), (app, layout, scale, frames)
                checked += 1
print(f"{checked} renders of recorded events without records or with shootout finals passed for {len(apps)} apps")
