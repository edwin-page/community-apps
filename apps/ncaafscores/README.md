<!-- community-maintenance:start -->
## Community maintenance

This community-maintained version includes updates to Starlark source, previews, compared with the shared Tronbyt ancestor in the September 21, 2026 audit. Original author and license notices remain in the source, manifest, and any original documentation below. Maintenance credit does not replace original authorship.

Original authors and other contributors can follow [Updating your app](../../docs/UPDATING_YOUR_APP.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md). Preserve app IDs, settings compatibility, original credits, and applicable licenses. Describe changes and actual test results in your pull request.

See [known compatibility differences](../../docs/COMPATIBILITY.md) and [maintenance history](../../docs/MAINTENANCE.md). These notes do not certify live integration or compatibility with every runtime. Earlier setup instructions below may describe the upstream version.
<!-- community-maintenance:end -->

# NCCAF Scores for Tidbyt

Displays live NCAAF scores and gambling odds for upcoming games. Updated every 2 minutes. No API key required.

![NCAAF Scores for Tidbyt](screenshot.png)



### September 21 score-data resilience

Edwin adapted the missing-odds and series-summary fixes from [Luke Solomon’s upstream change](https://github.com/tronbyt/apps/commit/edf5e1f5cb7ff319e8d805ae6a6f7325b1a51cf2) across the score apps. Missing optional odds, series summaries, or notes no longer abort playback. Unavailable odds stay blank; scores and final status remain visible. Existing settings, game ordering, and card timing are preserved. Offline missing-field and full-sequence renders are covered by `tests/sports_playback.py`; this does not certify provider availability or physical display playback.

Live score replacement between cards is enabled with League Name or Game Info headers. Current Time headers keep complete snapshot playback: their predicted per-card clocks must not be rebased midway through a sequence. Refresh scheduling remains independent of playback in all modes.

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

Downstream change, original authorship retained. The logo bundle in `logos/`
(added on 6 October) covered FBS and FCS teams as ESPN's team list names them.
Production logs for the last three days showed the app still downloading 14
logos on every render. Air Force's alternate logo was one of them, on 29
installations: the team list calls Air Force `AF` but the scoreboard says
`AFA`. UT Rio Grande Valley was missing from the team list, and twelve
Division II/III teams were not bundled at all. Their ESPN originals are
500x500 PNGs of up to 185 KB, each decoded and resized per render.
`tools/college_logos/build.py` now also collects every team on the 2026
regular-season FBS, FCS and Division II/III scoreboards (weeks 1-16), using
the abbreviation the feed reports. It adds the Division II/III team list
(ESPN group 35) and every alternate-logo team. The bundle grows from 266 to
668 logo URLs and from 798 to 2,004 PNGs (2,602,055 bytes; 12-32 pixels). The
existing 798 images are unchanged, and every logo URL production requested in
the last three days is now bundled. Every option in the Conference setting is
covered, Division II/III included. Regenerate or verify with
`python3 tools/college_logos/build.py --runtime <niblet> [--cache DIR] [--check] ncaafscores`.
A team, URL or size missing from the bundle (for example a team first scheduled
later, or a non-NCAA opponent) is still fetched as before. Settings, ordering,
timing and artwork are unchanged. A logo that ESPN or another host later
redraws at the same URL stays at the bundled version until the bundle is
regenerated. Reading the larger pack and index adds about 0.4 ms to each
render's module load (0.37 to 0.74 ms, measured locally).

Validation: `tools/college_logos/verify.py` rendered every bundled image and
its original download at 1x and 2x and got byte-identical WebP output.
`tests/college_logo_bundles.py` passes, and `build.py --check` matches the
committed files. `tools/college_logos/parity.py` rendered the previous and new
source from the same recorded responses: today's feeds plus every
conference's 2026 week-5 scoreboard. It covered every layout and header,
pre-game modes, the Top 25, FBS, FCS, Division II/III and five conference feeds
(Mountain West and Southland included), the ranking toggle and six team-focus
samples with timezones. At three pinned times and both scales, 528 of 528 WebP
outputs were byte-identical, with no request outside the recording. A
Division II/III render now reads one input instead of up to 256. The
Division II/III samples use no pre-game line. With the default record line,
both versions fail when an opponent's feed entry has no `records`. That is an
existing app limitation, and this change leaves it as it was. Physical-screen
playback is not covered by these checks.
