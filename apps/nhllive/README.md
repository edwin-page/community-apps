# NHL Live Applet for Tidbyt

Displays live game stats or next scheduled NHL game information.

![NHL Live Applet for Tidbyt](screenshot.png)
## Timezone settings (September 2026)

Timezone is now a searchable IANA timezone setting. Leave it blank to follow the display timezone. Existing installations retain their previous effective timezone through the reviewed Cloud migration.

Downstream change, original authorship retained. Requires the Niblet runtime with timezone Text metadata. All changed schemas were evaluated with networking denied. Migration and rendering evidence is recorded in the timezone release audit; schema checks alone do not certify live provider behavior.

### Bundled pre-resized team logos (October 2026)

Downstream change, original authorship retained. The ESPN logo of every team in
`TEAMS_LIST` (all 32 clubs, using the same `abbr_fix` URLs) is packaged in
`images/logos/` at the 18-pixel size the game screen draws it, produced by the
runtime's own nearest-neighbour resize from the same source URLs; `logos.star`
lists each source URL and its SHA-256. Regenerate or verify with
`cd tools/lunchbox_logos && go run . -app nhllive [-check]`. Renders no longer
request the two team logos. A logo URL missing from the bundle is still
fetched from ESPN as before, with the NHL logo as the failure fallback.
Settings, schedule requests, caching, timing and artwork are unchanged; a logo
ESPN later redraws at the same URL stays at the bundled version until the
bundle is regenerated.

Validation: `tools/lunchbox_logos/parity.py` rendered the previous and new
source from the same recorded NHL and ESPN responses: today's schedules
(2026-10-12), the week of 2026-03-02 as final, live (boxscore state, clock and
situation rewritten), pre-game, and an empty week falling back to the season
schedule, for all 32 teams, both toggles and two timezones, at three pinned
times: 540 of 540 WebP outputs were byte-identical, with no request outside the
recording, and all 32 bundled logos were drawn. "Shuffle All Teams" and the
live stat line choose with `random.number`, so the shuffle option was left out
and each configuration enabled a single live stat (all eight covered). The
app does not declare 2x support, so only 1x was rendered. Physical-screen
playback is not covered by these checks.
