"""Byte-identical render check for the bundled LunchBox league logos.

Usage, from the repository root:

  python3 tools/lunchbox_logos/parity.py RUNTIME APP --snapshots DIR [--base REV] [--record]

Renders apps/APP at a base revision (default origin/main) and in the working
tree with `render --input-snapshot`, so both read the same recorded responses,
and requires identical WebP bytes for every configuration, time and scale in
the matrix. RUNTIME must support --input-snapshot, --metadata-output and --now.

--record builds DIR/APP/<scenario>/ (index.json plus bodies named by SHA-256):
the base version is rendered repeatedly and every request it makes that the
snapshot lacks is fetched once and added, until it is served entirely from the
snapshot. Scenarios (see SCENARIOS below) are "live" (today's feeds) and, for
scoreboard apps, feeds for other dates served at the app's default scoreboard
URL, chosen so that every team (and so every bundled logo) and pre-game, live
and final cards are drawn. Later runs replay offline; any request either
version makes outside the snapshot fails the check.

Apps with "feed": "source" in apps.json (logo URLs from team tables in the
source) use SOURCE_APPS below instead: every team option and toggle, and
scenarios whose recorded responses are real provider bodies for chosen dates,
with the game state optionally rewritten so pre-game, live, final and no-game
screens are all drawn for every team. Both versions read the same recording.

Prints, per app, the number of identical renders and the metadata deltas
(inputs, reads.time) between the two versions.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import io
import itertools
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request

root = Path(__file__).resolve().parents[2]
CONFIG = json.loads((root / "tools/lunchbox_logos/apps.json").read_text())
NOWS = ["2026-10-06T18:00:00Z", "2026-10-11T16:30:00Z", "2026-10-07T03:59:30Z"]
TIMEZONES = ["", "America/New_York", "America/Los_Angeles"]

# Extra scoreboard bodies (merged ESPN daily feeds) served at the default URL.
SCENARIOS = {
    "nflscores": {"week1": ["20250904", "20250907", "20250908"], "upcoming": ["20261011"]},
    "nhlscores": {"allteams": ["20260301", "20260302", "20260303"], "upcoming": ["20261010"]},
    "mlbscores": {"allteams": ["20260801", "20260802"], "postseason": ["20261006"]},
    "nbascores": {"allteams": ["20260301", "20260302", "20260303", "20260304"], "upcoming": ["20261021"]},
    "wnbascores": {"allteams": ["20260701", "20260702", "20260703", "20260705"]},
    "cflscores": {"allteams": ["20220804", "20220805", "20220806", "20220812", "20220813"], "upcoming": ["20261010"]},
    "mlsscores": {"allteams": ["20260801", "20260802", "20260815", "20260816"], "upcoming": ["20261018"]},
    "uflscores": {"allteams": ["20260328", "20260329", "20260404", "20260405"]},
    "xflscores": {"allteams": ["20230218", "20230219", "20230225", "20230226"]},
    "wbcscores": {"allteams": ["20260305", "20260306", "20260307", "20260308", "20260309"]},
    "mhkyscores": {"allteams": ["20260109", "20260110", "20260116", "20260117"]},
}


def sha(body):
    return hashlib.sha256(body).hexdigest()


class Snapshot:
    def __init__(self, directory):
        self.dir = Path(directory)
        index = self.dir / "index.json"
        self.entries = {e["url"]: e for e in json.loads(index.read_text())["entries"]} if index.exists() else {}

    def add(self, url, status, body):
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / sha(body)).write_bytes(body)
        self.entries[url] = {"url": url, "method": "GET", "status": status, "sha256": sha(body)}
        (self.dir / "index.json").write_text(json.dumps({"schema": "niblet.input-snapshot.v1", "entries": list(self.entries.values())}, indent=1))


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Go-http-client/1.1"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            # Rate limits and server errors are retried rather than recorded.
            if (error.code == 429 or error.code >= 500) and attempt < 5:
                time.sleep(2 ** attempt * 2)
                continue
            return error.code, error.read()


def merged_feed(league, dates, exclude=()):
    events, seen = [], set()
    doc = None
    for day in dates:
        status, body = fetch(f"https://site.api.espn.com/apis/site/v2/sports/{league}/scoreboard?dates={day}")
        assert status == 200, (league, day, status)
        doc = json.loads(body)
        for event in doc.get("events", []):
            teams = {c["team"].get("abbreviation") for c in event["competitions"][0]["competitors"]}
            # Teams without an ESPN logo make both versions fail the render; skip them.
            if event["id"] not in seen and not teams & set(exclude):
                seen.add(event["id"])
                events.append(event)
    doc["events"] = events
    return json.dumps(doc).encode()


def render(runtime, main, out, config, now, scale, snapshot, metadata):
    args = [runtime, "render", str(main), "-o", str(out), "--now", now, "--metadata-output", str(metadata),
            "--timeout", "60s", "--silent"]
    if snapshot:
        args += ["--input-snapshot", str(snapshot)]
    if scale == 2:
        args.append("-2")
    args += [f"{k}={v}" for k, v in config.items()]
    result = subprocess.run(args, capture_output=True, text=True, env={**os.environ, "PIXLET_IMAGE_CACHE_DIR": ""})
    if result.returncode != 0:
        return None, result.stderr[-2000:]
    return json.loads(Path(metadata).read_text()), None


def base_copy(revision, app, destination):
    archive = subprocess.check_output(["git", "archive", revision, "apps/" + app], cwd=root)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(destination, filter="data")
    return destination / "apps" / app / CONFIG[app]["source"]


def options(runtime, main, field_id):
    schema = json.loads(subprocess.check_output([runtime, "schema", str(main)], stderr=subprocess.DEVNULL))
    for field in schema["schema"]:
        if field["id"] == field_id:
            return [o["value"] for o in field.get("options", [])]
    return []


def matrix(runtime, main, app):
    display_types = options(runtime, main, "displayType")
    tops = options(runtime, main, "displayTop")
    pregame = options(runtime, main, "pregameDisplay")
    teams = options(runtime, main, "selectedTeam")
    configs = []
    # Every layout with every header.
    for display_type, top in itertools.product(display_types or [None], tops or [None]):
        configs.append({"displayType": display_type, "displayTop": top})
    # Pre-game variants on logo layouts.
    for display_type, pre in itertools.product(display_types[:3] or [None], pregame):
        configs.append({"displayType": display_type, "pregameDisplay": pre})
    # Team focus (including local and magnified logos) and timezones.
    focus = [t for t in teams if t not in ("all", "")]
    for i, team in enumerate(focus[:: max(1, len(focus) // 6)] + [t for t in ("IND", "LAR", "CAR", "NYG") if t in focus]):
        configs.append({"selectedTeam": team, "displayType": (display_types or [None])[i % max(1, len(display_types))],
                        "timezone": TIMEZONES[i % 3], "rotationSpeed": str(3 + i % 5)})
    # Standings: every division grouping, cycling the rows per card and headers.
    divisions = options(runtime, main, "divisionType")
    rows = options(runtime, main, "teamsOptions")
    for i, division in enumerate(divisions):
        configs.append({"divisionType": division, "teamsOptions": rows[i % len(rows)] if rows else None,
                        "displayTop": tops[i % len(tops)] if tops else None})
    for i, tz in enumerate(TIMEZONES[1:]):
        configs.append({"timezone": tz, "displayTop": "time" if "time" in tops else None, "displayType": (display_types or [None, None])[i]})
    return [{k: v for k, v in c.items() if v is not None} for c in configs]


def record(runtime, base_main, app, directory, configs):
    cfg = CONFIG[app]
    scenarios = {"live": None}
    if cfg["feed"] == "scoreboard":
        scenarios.update(SCENARIOS.get(app, {}))
    for name, dates in scenarios.items():
        snap = Snapshot(directory / app / name)
        if dates and not snap.entries:
            # Learn the default scoreboard URL from a live render, then serve the merged body there.
            meta, err = render(runtime, base_main, directory / "probe.webp", {}, NOWS[0], 1, None, directory / "probe.json")
            assert meta, err
            feed = next(i["url"] for i in meta["inputs"] if "/scoreboard" in i["url"] and "dates=" not in i["url"])
            snap.add(feed, 200, merged_feed(cfg["league"], dates, cfg.get("parity_exclude_teams", ())))
        for _ in range(6):
            missing = set()
            # Team focus requests calendar windows, so discover them at every pinned time.
            probes = [(c, NOWS[0]) for c in configs[:: max(1, len(configs) // 12)]]
            probes += [(c, now) for c in configs if "selectedTeam" in c for now in NOWS]
            for config, now in probes:
                meta, err = render(runtime, base_main, directory / "probe.webp", config, now, 1, snap.dir if snap.entries else None, directory / "probe.json")
                if meta is None:
                    print(f"{app}/{name}: record render failed {config}: {err}", file=sys.stderr)
                    continue
                missing |= {i["url"] for i in meta["inputs"] if i["url"] not in snap.entries}
            if not missing:
                break
            for url in sorted(missing):
                snap.add(url, *fetch(url))
        print(f"{app}/{name}: {len(snap.entries)} recorded responses")


# ---------------------------------------------------------------------------
# "feed": "source" apps. A scenario is a hook(url) returning (status, body) to
# record for that URL, or None to record the live response unchanged.

MLB_STATE = {"Preview": ("Scheduled", "S"), "Live": ("In Progress", "I"), "Final": ("Final", "F")}


def json_body(url):
    status, body = fetch(url)
    assert status == 200, (url, status)
    return json.loads(body)


def mlb_live_linescore(ls):
    ls.update({"currentInning": 7, "isTopInning": False, "balls": 2, "strikes": 1, "outs": 1})
    ls["offense"] = {**ls.get("offense", {}), "first": {"id": 1, "fullName": "A Runner"}, "third": {"id": 2, "fullName": "B Runner"}}


def mlb_set_state(doc, state):
    for day in doc.get("dates", []):
        for game in day.get("games", []):
            detailed, code = MLB_STATE[state]
            game["status"].update({"abstractGameState": state, "detailedState": detailed, "codedGameState": code, "statusCode": code})
            if state == "Preview":
                game.pop("linescore", None)
                for side in ("away", "home"):
                    game["teams"][side].pop("score", None)
            elif state == "Live" and "linescore" in game:
                mlb_live_linescore(game["linescore"])


def mlb(day, state=None, next_state=None, no_games=False):
    """statsapi schedules for `day` (date-less URLs) or windows starting the day after (startDate URLs)."""
    def hook(url):
        if "statsapi.mlb.com/api/v1/schedule?" in url:
            window = re.search(r"startDate=([\d-]+)&endDate=([\d-]+)", url)
            if window:
                span = datetime.date.fromisoformat(window[2]) - datetime.date.fromisoformat(window[1])
                start = datetime.date.fromisoformat(day) + datetime.timedelta(days=1 if next_state else 0)
                doc = json_body(url.replace(window[0], f"startDate={start}&endDate={start + span}"))
                if next_state:
                    mlb_set_state(doc, next_state)
            else:
                doc = json_body(url + "&date=" + day)
                if state:
                    mlb_set_state(doc, state)
            if no_games:
                doc["dates"], doc["totalGames"] = [], 0
            return 200, json.dumps(doc).encode()
        if state == "Live" and re.search(r"/api/v1/game/\d+/linescore$", url):
            doc = json_body(url)
            mlb_live_linescore(doc)
            return 200, json.dumps(doc).encode()
        return None
    return hook


def nhl(week, state=None, empty_week=False):
    """api-web club week schedules for the week of `week`, games[0] optionally in `state`."""
    def hook(url):
        if re.search(r"/v1/club-schedule/\w+/week/now$", url):
            doc = json_body(url.replace("/week/now", "/week/" + week))
            if empty_week:
                doc["games"] = []
            elif state and doc["games"]:
                doc["games"][0]["gameState"] = state
            return 200, json.dumps(doc).encode()
        if state == "LIVE" and url.endswith("/boxscore"):
            doc = json_body(url)
            doc["gameState"] = "LIVE"
            doc["clock"] = {"timeRemaining": "07:42", "secondsRemaining": 462, "running": True, "inIntermission": False}
            doc["periodDescriptor"] = {"number": 2, "periodType": "REG", "maxRegulationPeriods": 3}
            doc["situation"] = {"situationCode": "1451"}
            return 200, json.dumps(doc).encode()
        return None
    return hook


def team_configs(runtime, main, field, extra):
    teams = [t for t in options(runtime, main, field) if t not in ("0", "")]
    configs = [{field: t} for t in teams]
    for i, more in enumerate(extra):
        configs.append({field: teams[(7 * i + 3) % len(teams)], **more})
    return configs


NHL_STATS = ["sog", "pim", "ppg", "fo", "hit", "blk", "take", "give"]

SOURCE_APPS = {
    "mlb_game": {
        "configs": lambda runtime, main: [{}] + team_configs(runtime, main, "team", [
            {"gameday_only": "true"}, {"include_exhibition_opponents": "true"},
            {"timezone": "America/Los_Angeles"}, {"timezone": "America/Chicago", "gameday_only": "true"}]),
        "scenarios": {
            "final": mlb("2026-08-01", "Final"), "live": mlb("2026-08-01", "Live"),
            "pregame": mlb("2026-08-02", "Preview"), "nogame": mlb("2026-08-01", no_games=True),
        },
    },
    "nhllive": {
        # random.number picks the team for "Shuffle All Teams" (0) and the live
        # stat among those enabled, so 0 is left out and each config enables
        # exactly one stat (cycling through all eight).
        "configs": lambda runtime, main: [
            {**c, **{stat: str(stat == NHL_STATS[i % len(NHL_STATS)]).lower() for stat in NHL_STATS}}
            for i, c in enumerate(team_configs(runtime, main, "teamid", [
                {"liveupdates": "false"}, {"gameday": "true"}, {"timezone": "America/Los_Angeles"},
                {"timezone": "Europe/Helsinki", "liveupdates": "false"}]))],
        "scenarios": {
            "final": nhl("2026-03-02"), "live": nhl("2026-03-02", "LIVE"),
            "pregame": nhl("2026-03-02", "FUT"), "season": nhl("2026-03-02", empty_week=True),
        },
    },
    "mlbnextgames": {
        "configs": lambda runtime, main: [{}] + team_configs(runtime, main, "team", []),
        "scenarios": {"aug": mlb("2026-08-01"), "sep": mlb("2026-09-20"), "apr": mlb("2026-04-10")},
    },
}


def record_source(runtime, base_main, app, directory, configs):
    spec = SOURCE_APPS[app]
    directory.mkdir(parents=True, exist_ok=True)
    for name, hook in {"today": None, **spec["scenarios"]}.items():
        snap = Snapshot(directory / app / name)
        for step in range(6):
            # The first round (live network) probes one time only, to stay under provider rate limits.
            probes = [(c, now) for c in configs for now in (NOWS[:1] if step == 0 and not snap.entries else NOWS)]

            def probe(job):
                (config, now), index = job
                out = directory / f"probe-{index}"
                meta, err = render(runtime, base_main, out.with_suffix(".webp"), config, now, 1,
                                   snap.dir if snap.entries else None, out.with_suffix(".json"))
                if meta is None:
                    print(f"{app}/{name}: record render failed {config} {now}: {err}", file=sys.stderr)
                    return set()
                return {i["url"] for i in meta["inputs"] if i["url"] not in snap.entries}

            with concurrent.futures.ThreadPoolExecutor(8 if snap.entries else 2) as pool:
                missing = set().union(*pool.map(probe, [(p, i) for i, p in enumerate(probes)]))
            if not missing:
                break
            for url in sorted(missing):
                snap.add(url, *((hook and hook(url)) or fetch(url)))
        print(f"{app}/{name}: {len(snap.entries)} recorded responses")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime")
    parser.add_argument("apps", nargs="+")
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
            cfg = CONFIG[app]
            base_main = base_copy(args.base, app, tmp / "base")
            new_main = root / "apps" / app / cfg["source"]
            source = cfg["feed"] == "source"
            configs = SOURCE_APPS[app]["configs"](runtime, base_main) if source else matrix(runtime, base_main, app)
            if args.record:
                (record_source if source else record)(runtime, base_main, app, args.snapshots, configs)
            scenarios = sorted(p.name for p in (args.snapshots / app).iterdir() if (p / "index.json").exists())
            jobs = [(s, c, now, scale) for s in scenarios for c in configs for now in NOWS for scale in cfg["scales"]]

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
                same = out["base"][0] == out["new"][0]
                return job, (same, out["base"][1], out["new"][1], len(out["base"][0])), None

            identical, empty, deltas = 0, 0, {}
            with concurrent.futures.ThreadPoolExecutor(args.jobs) as pool:
                for job, result, err in pool.map(lambda p: run(*p), [(j, i) for i, j in enumerate(jobs)]):
                    if err:
                        print(f"{app}: FAIL {job}: {err}")
                        failed = True
                        continue
                    same, mb, mn, size = result
                    if not same:
                        print(f"{app}: DIFFERENT WebP {job}")
                        failed = True
                        continue
                    identical += 1
                    empty += mb["frame_count"] == 0
                    key = (len(mb["inputs"]), mb["reads"]["time"], len(mn["inputs"]), mn["reads"]["time"])
                    deltas[key] = deltas.get(key, 0) + 1
            print(f"{app}: {identical}/{len(jobs)} renders byte-identical ({empty} empty) across {len(scenarios)} scenarios {scenarios}, "
                  f"{len(configs)} configs, {len(NOWS)} times, scales {cfg['scales']}")
            for (bi, bt, ni, nt), count in sorted(deltas.items()):
                print(f"{app}:   inputs {bi} -> {ni}, reads.time {bt} -> {nt}: {count} renders")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
