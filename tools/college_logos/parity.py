"""Byte-identical render check for the bundled college football logos.

Usage, from the repository root:

  python3 tools/college_logos/parity.py RUNTIME APP [APP ...] --snapshots DIR [--base REV] [--record]

The college counterpart of tools/lunchbox_logos/parity.py, whose snapshot
recording and render helpers it reuses: apps/APP is rendered at a base revision
(default origin/main) and in the working tree with `render --input-snapshot`,
so both read the same recorded responses, and every configuration, pinned time
and scale must give identical WebP bytes. Any request outside the snapshot
fails the check. RUNTIME must support --input-snapshot, --metadata-output and
--now.

--record fills DIR/APP/<scenario>/ by rendering the base version until it is
served entirely from the snapshot. Scenario "live" holds today's feeds. For
NCAAF Scores, scenario "week5" serves each conference's 2026 week-5 scoreboard
at the URL the app requests, so another set of teams (and logos) is drawn.
"""
import argparse
import concurrent.futures
import importlib.util
import io
import itertools
import json
import subprocess
from pathlib import Path
import sys
import tarfile
import tempfile
import time

root = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True  # keep tools/lunchbox_logos free of __pycache__
spec = importlib.util.spec_from_file_location("lunchbox_parity", root / "tools/lunchbox_logos/parity.py")
lunchbox = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lunchbox)
Snapshot, fetch, render = lunchbox.Snapshot, lunchbox.fetch, lunchbox.render

NOWS = ["2026-10-08T18:00:00Z", "2026-10-11T16:30:00Z", "2026-10-12T03:59:30Z"]
TIMEZONES = ["", "America/New_York", "America/Denver"]
SCALES = [1, 2]

# Top 25, FBS, FCS, Division II/III, Mountain West (Air Force), Southland
# (UT Rio Grande Valley), Big Ten, SEC and Big Sky.
CONFERENCES = ["0", "80", "81", "35", "17", "30", "5", "8", "20"]
# Air Force, UT Rio Grande Valley, West Alabama (Division II), Georgia
# (magnified logo), Iowa (alternate host) and Franklin Pierce (Division II).
FOCUS = ["2005", "292", "2695", "61", "2294", "112334"]


def ncaafscores_matrix():
    configs = []
    for i, (display_type, top) in enumerate(itertools.product(
            ["colors", "black", "logos", "horizontal", "stadium", "retro"], ["league", "time", "gameinfo"])):
        configs.append({"displayType": display_type, "displayTop": top, "conferenceType": CONFERENCES[i % len(CONFERENCES)]})
    for i, conference in enumerate(CONFERENCES):
        configs.append({"conferenceType": conference, "displayType": ["colors", "logos", "horizontal"][i % 3]})
    for i, (display_type, pre) in enumerate(itertools.product(["colors", "black", "logos"], ["record", "odds", "nothing"])):
        configs.append({"displayType": display_type, "pregameDisplay": pre, "conferenceType": CONFERENCES[(i + 2) % len(CONFERENCES)]})
    configs.append({"displayRanking": "false", "conferenceType": "0"})
    configs.append({"displayRanking": "false", "conferenceType": "35", "displayType": "black"})
    for i, team in enumerate(FOCUS):
        configs.append({"selectedTeam": team, "displayType": ["colors", "logos", "horizontal", "black"][i % 4],
                        "timezone": TIMEZONES[i % 3], "rotationSpeed": str(3 + i % 5)})
    # Division II/III configurations use the default pre-game records: an
    # opponent without "records" no longer fails the render (October 2026).
    return configs


def ncaafstandings_matrix():
    conferences = ["top25", "1", "151", "4", "5", "12", "15", "17", "9", "8", "37&0", "37&1"]
    configs = []
    for i, conference in enumerate(conferences):
        configs.append({"conferenceType": conference, "teamsOptions": ["2", "3", "4"][i % 3],
                        "displayTop": ["league", "time", "gameinfo"][i % 3]})
    for rows, top in itertools.product(["2", "3", "4"], ["league", "time", "gameinfo"]):
        configs.append({"conferenceType": "top25", "teamsOptions": rows, "displayTop": top})
    return configs


APPS = {
    "ncaafscores": ("ncaaf_scores.star", ncaafscores_matrix, {"week5": "&dates=2026&seasontype=2&week=5"}),
    "ncaafstandings": ("ncaaf_standings.star", ncaafstandings_matrix, {}),
}


def base_copy(revision, app, destination):
    archive = subprocess.check_output(["git", "archive", revision, "apps/" + app], cwd=root)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(destination, filter="data")
    return destination / "apps" / app / APPS[app][0]


def fetch_retrying(url):
    # ESPN occasionally answers 502; record only a settled response.
    for attempt in range(5):
        status, body = fetch(url)
        if status < 500:
            break
        time.sleep(3 * (attempt + 1))
    return status, body


def record(runtime, base_main, app, directory, configs):
    directory.mkdir(parents=True, exist_ok=True)
    scenarios = {"live": None}
    scenarios.update(APPS[app][2])
    for name, suffix in scenarios.items():
        snap = Snapshot(directory / app / name)
        for _ in range(8):
            missing = set()

            def probe(index, config, now):
                out = directory / f"probe-{app}-{index}"
                return config, render(runtime, base_main, out.with_suffix(".webp"), config, now, 1,
                                      snap.dir if snap.entries else None, out.with_suffix(".json"))

            probes = [(i, c, now) for i, (c, now) in enumerate((c, now) for c in configs for now in NOWS)]
            with concurrent.futures.ThreadPoolExecutor(8) as pool:
                for config, (meta, err) in pool.map(lambda p: probe(*p), probes):
                    if meta is None:
                        print(f"{app}/{name}: record render failed {config}: {err}", file=sys.stderr)
                        continue
                    missing |= {i["url"] for i in meta["inputs"] if i["url"] not in snap.entries}
            if not missing:
                break
            for url in sorted(missing):
                # The app's undated conference scoreboards get another week's body.
                source = url + suffix if suffix and "/scoreboard" in url and "dates=" not in url else url
                snap.add(url, *fetch_retrying(source))
        print(f"{app}/{name}: {len(snap.entries)} recorded responses")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime")
    parser.add_argument("apps", nargs="+", choices=sorted(APPS))
    parser.add_argument("--snapshots", required=True, type=Path)
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()
    runtime = str(Path(args.runtime).resolve())
    failed = False
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for app in args.apps:
            base_main = base_copy(args.base, app, tmp / "base")
            new_main = root / "apps" / app / APPS[app][0]
            configs = APPS[app][1]()
            if args.record:
                record(runtime, base_main, app, args.snapshots, configs)
            scenarios = sorted(p.name for p in (args.snapshots / app).iterdir() if (p / "index.json").exists())
            jobs = [(s, c, now, scale) for s in scenarios for c in configs for now in NOWS for scale in SCALES]

            def run(job, index):
                scenario, config, now, scale = job
                snap = args.snapshots / app / scenario
                out = {}
                for label, main_path in (("base", base_main), ("new", new_main)):
                    webp, meta = tmp / f"{app}-{index}-{label}.webp", tmp / f"{app}-{index}-{label}.json"
                    m, err = render(runtime, main_path, webp, config, now, scale, snap, meta)
                    if m is None:
                        return job, None, f"{label} failed: {err}"
                    offline = [i["url"] for i in m["inputs"] if i.get("source") != "snapshot"]
                    if offline:
                        return job, None, f"{label} requested outside snapshot: {offline[:3]}"
                    out[label] = (webp.read_bytes(), m)
                return job, (out["base"][0] == out["new"][0], out["base"][1], out["new"][1]), None

            identical, empty, deltas = 0, 0, {}
            with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
                for job, result, err in pool.map(lambda p: run(*p), [(j, i) for i, j in enumerate(jobs)]):
                    if err:
                        print(f"{app}: FAIL {job}: {err}")
                        failed = True
                        continue
                    same, mb, mn = result
                    if not same:
                        print(f"{app}: DIFFERENT WebP {job}")
                        failed = True
                        continue
                    identical += 1
                    empty += mb["frame_count"] == 0
                    key = (len(mb["inputs"]), len(mn["inputs"]))
                    deltas[key] = deltas.get(key, 0) + 1
            print(f"{app}: {identical}/{len(jobs)} renders byte-identical ({empty} empty) across {len(scenarios)} scenarios {scenarios}, "
                  f"{len(configs)} configs, {len(NOWS)} times, scales {SCALES}")
            for (bi, ni), count in sorted(deltas.items()):
                print(f"{app}:   inputs {bi} -> {ni}: {count} renders")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
