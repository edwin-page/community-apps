# MLB Next Games

Community app by Anthony Rocchio. Shows the selected team's next three games in
the coming week, with the day, start time and opponent logo, from the MLB Stats
API schedule and ESPN team logos.

## Bundled pre-resized team logos (October 2026)

Downstream change, original authorship retained. The logo of every team in
`TEAMS` (all 30 clubs, the same light or dark ESPN scoreboard URL the app
already used for each) is packaged in `images/logos/` at the 12-pixel size the
app draws it, produced by the runtime's own nearest-neighbour resize from the
same source URLs; `logos.star` lists each source URL and its SHA-256.
Regenerate or verify with `cd tools/lunchbox_logos && go run . -app
mlbnextgames [-check]`. Renders now make only the schedule request. A logo URL
or size missing from the bundle is still fetched from ESPN as before, with the
blank box as the failure fallback. Settings, schedule requests, timing and
artwork are unchanged; a logo ESPN later redraws at the same URL stays at the
bundled version until the bundle is regenerated.

Validation: `tools/lunchbox_logos/parity.py` rendered the previous and new
source from the same recorded MLB and ESPN responses: today's schedule windows
(2026-10-12, mostly off days) and the weeks starting 2026-04-10, 2026-08-01 and
2026-09-20, for all 30 teams and the default, at three pinned times: 372 of 372
WebP outputs were byte-identical, with no request outside the recording, and
all 30 bundled logos were drawn. The app does not declare 2x support, so only
1x was rendered. Physical-screen playback is not covered by these checks.
