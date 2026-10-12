<!-- community-maintenance:start -->
## Community maintenance

This community-maintained version includes updates to previews, compared with the shared Tronbyt ancestor in the September 21, 2026 audit. Original author and license notices remain in the source, manifest, and any original documentation below. Maintenance credit does not replace original authorship.

Original authors and other contributors can follow [Updating your app](../../docs/UPDATING_YOUR_APP.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md). Preserve app IDs, settings compatibility, original credits, and applicable licenses. Describe changes and actual test results in your pull request.

See [known compatibility differences](../../docs/COMPATIBILITY.md) and [maintenance history](../../docs/MAINTENANCE.md). These notes do not certify live integration or compatibility with every runtime. Earlier setup instructions below may describe the upstream version.
<!-- community-maintenance:end -->

## Bundled pre-resized team logos (October 2026)

Downstream change, original authorship retained. The ESPN logo of every team in
`ESPN_SLUGS` (all 30 clubs) is packaged in `images/logos/` at the two sizes the
app draws it, 20 pixels on the final card and 24 on the next-matchup card,
produced by the runtime's own nearest-neighbour resize from the same source
URLs; `logos.star` lists each source URL and its SHA-256. Regenerate or verify
with `cd tools/lunchbox_logos && go run . -app mlbliveticker [-check]`. Final
and next-game renders no longer download and resize the 500-pixel logos. A
logo URL or size missing from the bundle is still fetched from ESPN as before,
with the coloured initial block as the failure fallback. Settings, schedule
requests, timing and artwork are unchanged; a logo ESPN later redraws at the
same URL stays at the bundled version until the bundle is regenerated.

Validation: `tools/lunchbox_logos/parity.py` rendered the previous and new
source from the same recorded MLB and ESPN responses: today's schedules
(2026-10-12) and the 2026-08-01/02 schedules as final (with and without a
scheduled next game), live (state and count rewritten) and pre-game, for all
30 teams, the default, the off-day toggle and two timezones, at three pinned
times: 510 of 510 WebP outputs were byte-identical, with no request outside
the recording, and all 30 bundled logos were drawn at both sizes. The app does
not support 2x, so only 1x was rendered. Physical-screen playback is not
covered by these checks.
