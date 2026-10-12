# Fly The L

Borne out of a desire to be notified every time the Cubs lose, here is the app Fly The L!

On the rare occasions the Cubs win, you would see this:
![Cubs Win](W.gif)

When the Cubs lose you would see this:
![Cubs Lose](CubsL.gif)

But it also works for any team, such as the Orioles:
![Orioles Lose](OriolesL.gif)

You can see a preview of an upcoming game, you control the hour of the day it switches from showing you a previous result to the next game:
![Preview](preview.gif)

When a game is in progress, get LIVE updates!
![In-game updates](in-game-updates.gif)

Don't miss out on every drive into deep left field by Nick Castellanos!
![Castellanos](castellanos.gif)

## No games scheduled (October 2026)

Downstream change in this community-maintained version; original authorship
retained. Before the switch hour, the app read the first day of the team's
schedule for yesterday's result. When the team has no games in the next week
(the offseason, or after elimination from the postseason) MLB returns an empty
schedule, and every morning render failed with `index 0 out of range: empty
list` (`flythel.star:234`). It now shows the existing "no games for the next
week" screen, as it already did after the switch hour. Settings and every
other screen are unchanged.

Validation: the previous and new source were rendered from the same recorded
MLB schedule responses of 12 October 2026 for all 30 teams, three switch hours,
both game-time formats and three timezones at four pinned times (360 renders).
All 256 renders that the previous source completed were byte-identical; the
other 104 failed before on the empty schedule and now show the no-games screen.
No request fell outside the recording. The live in-game screen was not drawn
because no game was in progress when the responses were recorded.
Physical-screen playback is not covered by these checks.
