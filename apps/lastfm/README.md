<!-- community-maintenance:start -->
## Community maintenance

This community-maintained version includes updates to Starlark source, previews, compared with the shared Tronbyt ancestor in the September 21, 2026 audit. Original author and license notices remain in the source, manifest, and any original documentation below. Maintenance credit does not replace original authorship.

Original authors and other contributors can follow [Updating your app](../../docs/UPDATING_YOUR_APP.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md). Preserve app IDs, settings compatibility, original credits, and applicable licenses. Describe changes and actual test results in your pull request.

See [known compatibility differences](../../docs/COMPATIBILITY.md) and [maintenance history](../../docs/MAINTENANCE.md). These notes do not certify live integration or compatibility with every runtime. Earlier setup instructions below may describe the upstream version.
<!-- community-maintenance:end -->

## Album art fallback (October 2026)

Downstream change in this community-maintained version; original authorship
retained. Last.fm can return blank recent-track images when a scrobble has no
linked album, so the app never fetched art and showed a bright green square
for those tracks. Production showed four separate accounts making successful
recent-track calls for a month with no album-art fetch at all. When the
recent-track art is blank, the app now asks Last.fm's `track.getInfo` for the
track's album art (one extra call to the same API host, only in that case).
If no art exists anywhere, it shows a dark square instead of the green one.
Art is still only fetched from Last.fm's two image hosts. Settings are
unchanged.

Validation: `tests/lastfm_cover_art.py` renders recorded-shape responses
offline at 1x and 2x. It checks five cases: art present, blank art resolved
by `track.getInfo`, no art anywhere, a missing album, and a non-Last.fm image
host. The previous source fails the blank-art case. With art present, the
previous and new sources render byte-identical output (1x and 2x, clock on
and off). No live Last.fm key was used, so it is unconfirmed whether the
blank art seen in production comes from Last.fm or from the scrobbling
client. Physical-screen playback is not covered by these checks.
