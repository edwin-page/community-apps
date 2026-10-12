# MLB Game

Community app by ckelley-1992. Shows the selected team's game for the current
day with score, bases, count, and outs from the MLB Stats API, plus ESPN team
colors and logos.

## Niblet downstream changes (2026-09-30)

- When the selected team has no game today, the app shows the team with
  "No game" instead of a built-in sample game (PIT @ PHI, 1-3). With **Show
  only on game day** enabled, the app still hides itself instead.
- If the MLB schedule request fails, the app skips that render instead of
  showing sample data.
- Scheduled regular-season and postseason games are shown with their start
  time before MLB populates the linescore. Spring training and exhibition games
  still require a populated linescore.
- **Arizona Diamondbacks** now requests team 109. It previously requested 159
  (American League All-Stars), so Arizona never showed a game.
- Games are matched to the selected team by MLB team ID, not abbreviation.

No settings keys or saved values changed.

## Niblet downstream changes (2026-10-05)

- Team colours and scoreboard logos come from a constant table generated from
  ESPN's MLB teams endpoint, and the active MLB team ids from the existing
  `TEAM_BY_ID` table. The app no longer fetches and decodes the league-wide
  ESPN scoreboard and the statsapi team list on every render; it makes the
  schedule request plus the two logo requests.
- Output is unchanged whenever the game's teams are on ESPN's current
  scoreboard. When ESPN's scoreboard is still on the previous day (it rolled
  over later than MLB's schedule on 2026-10-05), the old app fell back to the
  built-in colour and the plain dark logo for those teams; it now always uses
  the ESPN colour and scoreboard logo. Regenerate the table if ESPN changes a
  team's colour or logo.

## Validation

On 2026-10-05, all 30 team settings rendered byte-identical WebPs before and
after the change from recorded MLB and ESPN responses for 2026-08-01 and
2026-09-20 (30 games each) and for 2026-10-05 once ESPN's scoreboard covers
that day. Against the live ESPN scoreboard, which still showed 2026-10-04, the
four teams playing on 2026-10-05 changed as described above and the other 26
were identical. Physical devices were not tested.

On 2026-09-30 (Wild Card day, four games), `niblet check`, `niblet lint`, and
`niblet format` passed with Niblet CLI v0.54.0. All 30 team settings rendered
at 1x against live data: the eight postseason teams showed their scheduled or
pre-game Wild Card game, and the other 22 showed "No game". The default
(no team) and 2x NYY renders completed. Live in-progress and final postseason
states, doubleheaders, and physical devices were not tested with this change.

## Bundled pre-resized team logos (October 2026)

Downstream change, original authorship retained. Every team logo URL the app
can request is packaged in `images/logos/` at the 14-pixel size the team tiles
draw it, produced by the runtime's own nearest-neighbour resize from the same
source URLs; `logos.star` lists each source URL and its SHA-256. That is 56
URLs: the ESPN dark scoreboard logos (via the combiner) for teams in
`ESPN_TEAM_META`, the plain dark ESPN logos used for the "No game" screen and
for codes ESPN does not list (`AZ`, `CWS`), and the four alternate Phillies,
Tigers, Reds and Cardinals logos. The Phillies and Tigers alternates are
palette PNGs whose resize the bundle cannot reproduce exactly, so their
original bytes are bundled and still resized at render time. Regenerate or
verify with `cd tools/lunchbox_logos && go run . -app mlb_game [-check]`.
Renders now make only the schedule request. A logo URL or size missing from
the bundle is still fetched as before. Settings, game selection, timing and
artwork are unchanged; a logo a provider later redraws at the same URL stays
at the bundled version until the bundle is regenerated.

Validation: `tools/lunchbox_logos/parity.py` rendered the previous and new
source from the same recorded responses: today's schedules (2026-10-12) and
the 2026-08-01/02 schedules as final, live (state and count rewritten),
pre-game and no-game screens, for all 30 teams, the default, both toggles and
two timezones, at three pinned times: 525 of 525 WebP outputs were
byte-identical, with no request outside the recording; 54 of the 56 bundled
URLs were drawn (the ESPN `ari` and `chw` keys are reached only if the
schedule ever reports `ARI` or `CHW`). The app does not declare 2x support, so
only 1x was rendered. Physical-screen playback is not covered by these checks.

## Known limitations

- Start times of 10:00 or later are clipped ("10:00E") in the status tile.
- The San Francisco logo is hard to see on the team's orange background.
