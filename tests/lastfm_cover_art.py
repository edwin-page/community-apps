"""Offline renders of Last FM recent tracks with and without album art.

python3 tests/lastfm_cover_art.py ../niblet-cli/niblet

Last.fm returns blank recent-track images when a scrobble has no linked album.
The app must then ask track.getInfo for the album art, and must only fetch art
from Last.fm's image hosts.
"""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
runtime = str(Path(sys.argv[1]).resolve())

ART = "https://lastfm.freetls.fastly.net/i/u/300x300/7c9c4d1009514b178c82f2201e3a1fce.jpg"
BLANK = [{"size": size, "#text": ""} for size in ("small", "medium", "large", "extralarge")]
SIZED = BLANK[:3] + [{"size": "extralarge", "#text": ART}]

def recent(images):
    track = {"name": "How Many More Times", "artist": {"#text": "Led Zeppelin"}, "image": images}
    return {"recenttracks": {"track": [track]}}

# name: (recent-track images, track.getInfo album images, expected requests)
CASES = {
    "recent art": (SIZED, None, ["user.getrecenttracks", ART]),
    "blank recent art": (BLANK, SIZED, ["user.getrecenttracks", "track.getInfo", ART]),
    "no art anywhere": (BLANK, BLANK, ["user.getrecenttracks", "track.getInfo"]),
    "missing album": (BLANK, "no album", ["user.getrecenttracks", "track.getInfo"]),
    "foreign host": ([{"size": "extralarge", "#text": "https://example.com/a.jpg"}], None, ["user.getrecenttracks"]),
}

overrides = '''
RECENT = json.decode(%s)
INFO = json.decode(%s)
def fake_get(url, params = {}):
    print("GET " + params.get("method", url))
    data = RECENT if params.get("method") == "user.getrecenttracks" else INFO
    def decoded():
        return data
    def body():
        return DEMOICON
    return struct(status_code = 200, json = decoded, body = body)
http = struct(get = fake_get)
'''

checked = 0
for name, (images, album_images, expected) in CASES.items():
    info = {"track": {"name": "x"}} if album_images == "no album" else {"track": {"album": {"image": album_images or []}}}
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        shutil.copytree(root / "apps/lastfm/images", tmp / "images")
        source = (root / "apps/lastfm/last_fm.star").read_text()
        source = source.replace('load("http.star", "http")\n', 'load("encoding/json.star", "json")\n', 1)
        source += overrides % (repr(json.dumps(recent(images))), repr(json.dumps(info)))
        (tmp / "last_fm.star").write_text(source)
        for scale in ([], ["-2"]):
            result = subprocess.run(
                [runtime, "render", str(tmp / "last_fm.star"), "lastFmUser=someone", "lastApiKey=key",
                 "--output", str(tmp / "out.webp"), "--timeout", "20s"] + scale,
                capture_output=True, text=True)
            assert result.returncode == 0, (name, result.stderr[-800:])
            requests = [line.split("GET ", 1)[1] for line in (result.stdout + result.stderr).splitlines() if "GET " in line]
            assert requests == expected, (name, requests)
            checked += 1
print(f"{checked} Last FM cover-art renders passed")
