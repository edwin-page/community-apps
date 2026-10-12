<!-- community-maintenance:start -->
## Community maintenance

This community-maintained version includes updates to Starlark source, compared with the shared Tronbyt ancestor in the September 21, 2026 audit. Original author and license notices remain in the source, manifest, and any original documentation below. Maintenance credit does not replace original authorship.

Original authors and other contributors can follow [Updating your app](../../docs/UPDATING_YOUR_APP.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md). Preserve app IDs, settings compatibility, original credits, and applicable licenses. Describe changes and actual test results in your pull request.

See [known compatibility differences](../../docs/COMPATIBILITY.md) and [maintenance history](../../docs/MAINTENANCE.md). These notes do not certify live integration or compatibility with every runtime. Earlier setup instructions below may describe the upstream version.
<!-- community-maintenance:end -->


### September 21 score-data resilience

Edwin adapted the missing-odds and series-summary fixes from [Luke Solomon’s upstream change](https://github.com/tronbyt/apps/commit/edf5e1f5cb7ff319e8d805ae6a6f7325b1a51cf2) across the score apps. Missing optional odds, series summaries, or notes no longer abort playback. Unavailable odds stay blank; scores and final status remain visible. Existing settings, game ordering, and card timing are preserved. Offline missing-field and full-sequence renders are covered by `tests/sports_playback.py`; this does not certify provider availability or physical display playback.

### Timezone setup (local change)

The Location prompt is replaced by an optional **Timezone** field. Leave it
blank to follow the device timezone, or enter an IANA name such as
`America/New_York` or `Europe/London`. A host that supplies no device timezone
uses UTC. Coordinates and city lookup are no longer needed.

Cloud's reviewed upgrade copies the old location timezone into the new field,
preserving saved choices and the previous New York default when no location was
saved. Clear the migrated field to follow the device instead. The app also
accepts a legacy location in direct render configurations when the new field
is absent. Teams, styling, ordering, card timing and refresh behavior are unchanged.
This requires a new catalog release and configuration migration; it is not live.

Validation: all 12 timezone/schema cases and the existing full sports playback
regression passed with the card-capable Niblet runtime, with network access
denied. Formatter and lint passed. Live provider and physical-screen checks
were not repeated for this setup-only change.

## Timezone settings (September 2026)

Timezone is now a searchable IANA timezone setting. Leave it blank to follow the display timezone. Existing installations retain their previous effective timezone through the reviewed Cloud migration.

Downstream change, original authorship retained. Requires the Niblet runtime with timezone Text metadata. All changed schemas were evaluated with networking denied. Migration and rendering evidence is recorded in the timezone release audit; schema checks alone do not certify live provider behavior.

### Bundled pre-resized team logos (October 2026)

Downstream change, original authorship retained. Every club crest the app
draws from ESPN for the 2026-27 Premier League clubs (and the transparent
placeholder) is packaged in `images/logos/` at each size the layouts draw it
(compact 13 or 16, 30 and 32 pixels), produced by the runtime's own
nearest-neighbour resize from the same source URLs; `logos.star` lists each
source URL and its SHA-256. This covers all 20 crest URLs production renders
requested from 9 to 12 October 2026. Regenerate or verify with
`cd tools/lunchbox_logos && go run . -app eplscores [-check]`. An all-teams
render now makes one request (the scoreboard, cached 60 seconds) instead of up
to 21, and Retro and Stadium, which draw no crests, no longer download them. A
crest URL or size missing from the bundle is still fetched from ESPN as before.
Settings, ordering, timing and artwork are unchanged; a crest ESPN later
redraws at the same URL stays at the bundled version until the bundle is
regenerated.

Validation: `tools/lunchbox_logos/parity.py` rendered the previous and new
source from the same recorded responses (live feed, all clubs from the first
two 2026-27 matchdays, and an October matchday) across every layout, header,
pre-game mode, team focus sample and timezone, on the 64x32 and square 64x64
canvases, at three pinned times: 702 of 702 WebP outputs were byte-identical,
with no request outside the recording. `tools/lunchbox_logos/verify.py`
rendered all 64 bundled URL and size pairs identically to the freshly
downloaded originals. The sports playback, timezone and sequence tests,
`niblet check`, format and lint also pass. Physical-screen playback is not
covered by these checks.
