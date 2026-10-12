<!-- community-maintenance:start -->
## Community maintenance

This community-maintained version includes updates to Starlark source, compared with the shared Tronbyt ancestor in the September 21, 2026 audit. Original author and license notices remain in the source, manifest, and any original documentation below. Maintenance credit does not replace original authorship.

The configuration schema differs from the audited upstream baseline. Check the current schema and test existing saved settings before switching versions; differences may include labels as well as behavior.

Original authors and other contributors can follow [Updating your app](../../docs/UPDATING_YOUR_APP.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md). Preserve app IDs, settings compatibility, original credits, and applicable licenses. Describe changes and actual test results in your pull request.

See [known compatibility differences](../../docs/COMPATIBILITY.md) and [maintenance history](../../docs/MAINTENANCE.md). These notes do not certify live integration or compatibility with every runtime. Earlier setup instructions below may describe the upstream version.
<!-- community-maintenance:end -->

# Men's soccer tournament / league

Men's soccer displays upcoming / current / completed games for tourname / league you have selected

Displayed:

- Home / Away Teams & current standings
- If future game: Date & Time of upcoming game
- If inprogress game:  Score & Time
- If past game:  Final Score

## Configuration
- Select League / Tournament to display.  Current Leagues / Tournament options are:
    * Dutch Eredivisie
    * English Carabo Cup
    * English FA Cup
    * English League Championship
    * English League One
    * English League Two
    * English National League
    * English Premiere League
    * French Ligue 1
    * FIFA World Cup
    * German Bundesliga
    * Italian Serie A
    * Mexican Liga BBVA MX
    * Scottish Premiership
    * Spanish LaLiga
    * UEFA Champions League
    * UEFA Europa League

- Which team to display first (home or away)
- Select display format type
- Select color for time
- Select time to display each score (this eliminates the mult-instance thing we've traditionally done)
- 12 hour vs 24 hour time & US vs Intl date format
- Select if you want to show a range of days forward / back instead of just the default API results & specify how many days forward and back.

## Thanks

Thanks a lot to a bunch of folks who have worked on these various sports apps.  @LunchBox8484 is the original author of many of them.
Thanks to @jesushairdo for the new option to be able to show home or away team first.  Let's be more international :-)

## Screenshot

![screenshot](soccermens.gif)
![screenshot](soccermens2.gif)


### September 21 score-data resilience

Edwin adapted the missing-odds and series-summary fixes from [Luke Solomon’s upstream change](https://github.com/tronbyt/apps/commit/edf5e1f5cb7ff319e8d805ae6a6f7325b1a51cf2) across the score apps. Missing optional odds, series summaries, or notes no longer abort playback. Unavailable odds stay blank; scores and final status remain visible. Existing settings, game ordering, and card timing are preserved. Offline missing-field and full-sequence renders are covered by `tests/sports_playback.py`; this does not certify provider availability or physical display playback.

### Bundled pre-resized team logos (October 2026)

Downstream change, original authorship retained. The club crests and national
flags of every team ESPN lists for the 47 league and tournament options (the
`comps.json` list as of 12 October 2026, plus each competition's current
scoreboard), 749 URLs in all, are packaged in `images/logos/` at each size the
layouts draw them (16 for Team Colors and Black, 30, 32 for Horizontal, 16 for
Wide 3 and 9 for Wide 4), produced by the runtime's own nearest-neighbour
resize from the same source URLs. The files are stored in about 128 KB
`pack-NN.bin` shards; `logos.star` records each source URL, its SHA-256 and the
byte range of each size, so a render reads only the shards it draws from
instead of loading thousands of files. This covers 167 of the 168 logo URLs
production renders requested from 9 to 12 October 2026 (the GIF below is the
exception). Regenerate or verify with
`cd tools/lunchbox_logos && go run . -app soccermens [-check]`.

Retro, which draws no logos, no longer downloads a bundled one. A logo URL or
size missing from the bundle is still fetched as before. Two placeholder URLs
are deliberately not bundled because they do not return an image:
`upload.wikimedia.org/.../1x1.png?src=soccermens` (used when ESPN reports an
empty logo) returns 403 to the runtime's HTTP client, so those renders keep
failing exactly as they do today, and ESPN's `ncaa_football` placeholder
returns 404. One crest that ESPN serves as a GIF (`soccer/500/635.png`) is also
left to the network because the runtime decodes GIFs on a different path.
Settings, ordering, timing and artwork are unchanged; a logo ESPN later redraws
at the same URL stays at the bundled version until the bundle is regenerated.

Validation: `tools/lunchbox_logos/parity.py` rendered the previous and new
source from the same recorded responses (the live scoreboards of every option)
for every league with every layout, plus calendar windows, team order, date
formats and team-colour samples, at three pinned times and at 1x and 2x:
1666 of 1666 successful WebP outputs were byte-identical, with no request
outside the recording. The other 188 of the 1854 renders failed identically in
both versions: 122 on the Wikimedia 403 above, 42 on the `zzz.donotuse` option
in the league list and 24 on Wide 3/4 penalty-shootout finals
(`string + int`); none of these is changed here. `tools/lunchbox_logos/verify.py`
rendered all 2996 bundled URL and size pairs identically to the freshly
downloaded originals. The sports playback and sequence tests, `niblet check`,
format and lint also pass. Physical-screen playback is not covered by these
checks.
