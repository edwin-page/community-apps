<!-- community-maintenance:start -->
## Community maintenance

This community-maintained version includes updates to manifest, previews, compared with the shared Tronbyt ancestor in the September 21, 2026 audit. Original author and license notices remain in the source, manifest, and any original documentation below. Maintenance credit does not replace original authorship.

Original authors and other contributors can follow [Updating your app](../../docs/UPDATING_YOUR_APP.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md). Preserve app IDs, settings compatibility, original credits, and applicable licenses. Describe changes and actual test results in your pull request.

See [known compatibility differences](../../docs/COMPATIBILITY.md) and [maintenance history](../../docs/MAINTENANCE.md). These notes do not certify live integration or compatibility with every runtime. Earlier setup instructions below may describe the upstream version.
<!-- community-maintenance:end -->

# NCCAF Standings for Tidbyt

Displays live NCAAF standings by conference.

![NCAAF Standings for Tidbyt](screenshot.png)


### Bundled pre-resized team logos (October 2026)

Downstream change, original authorship retained. The 10-pixel logo bundle in
`logos/` (added on 6 October) was built from ESPN's team list, whose
abbreviations do not always match the standings feeds the app reads: Air Force
is `AF` in the list but `AFA` in the feeds, so its alternate logo was still
downloaded on every render (five installations in the last three days of
production logs). `tools/college_logos/build.py` now also collects teams from
the Top 25 and every conference standings feed the settings offer, and adds
every alternate-logo team. The bundle grows from 139 to 149 logo URLs (57,635
bytes of PNGs): Air Force and the rest of the app's alternate-logo table (eight
FCS teams, and Wisconsin's entry, which the feeds do not select because they
report `WIS`). The existing 139 images are unchanged. Every logo URL production requested in
the last three days is now bundled. Regenerate or verify with
`python3 tools/college_logos/build.py --runtime <niblet> [--cache DIR] [--check] ncaafstandings`.
A URL or size missing from the bundle is still fetched as before, and the
per-team colour requests are unchanged. Settings, ordering, timing and artwork
are unchanged. A logo that ESPN or another host later redraws at the same URL
stays at the bundled version until the bundle is regenerated.

Validation: `tools/college_logos/verify.py` rendered every bundled image and
its original download at 1x and 2x and got byte-identical WebP output.
`tests/college_logo_bundles.py` passes, and `build.py --check` matches the
committed files. `tools/college_logos/parity.py` rendered the previous and new
source from the same recorded responses. It covered every conference option,
the Top 25, 2-4 rows per page and every header, at three pinned times and both
scales: 126 of 126 WebP outputs were byte-identical, with no request outside
the recording. Physical-screen playback is not covered by these checks.
