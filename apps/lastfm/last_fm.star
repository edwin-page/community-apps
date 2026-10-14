# Modified in this community-maintained version; see Git history for contributors.
# Original author and license notices are retained below.
# See README.md for maintenance and compatibility notes.

"""
Applet: Last FM
Summary: Show Last.fm history
Description: Show title, artist and album art from most recently scrobbled song in your Last.fm history.
Author: Chuck
"""

load("http.star", "http")
load("images/demoicon.jpg", DEMOICON_ASSET = "file")
load("render.star", "render")
load("schema.star", "schema")
load("time.star", "time")

DEMOICON = DEMOICON_ASSET.readall()

LASTFM_API = "https://ws.audioscrobbler.com/2.0/"
ART_HOSTS = ("https://lastfm.freetls.fastly.net/", "https://lastfm-img2.akamaized.net/")

def largest_image_url(images):
    # Last.fm lists sizes small to large; take the largest one that is set.
    for image in reversed(images or []):
        url = image.get("#text", "") if type(image) == "dict" else ""
        if url:
            return url
    return ""

def main(config):
    userName = config.get("lastFmUser") or "badUser"
    api_key = config.get("lastApiKey") or "badKey"
    clockShown = config.bool("showClock", True)

    if (userName == "DemoUser" or api_key == "DemoKey"):
        return demoMode()

    # handle missing config data
    if (userName == "badUser"):
        return render.Root(
            child = render.WrappedText(
                content = "Last.fm Username missing in Tidbyt config. Use DemoUser for demo.",
                color = "#FF0000",
                font = "tom-thumb",
            ),
        )
    if (api_key == "badKey"):
        return render.Root(
            child = render.WrappedText(
                content = "Last.fm API key missing in Tidbyt config. Use DemoKey for demo.",
                color = "#FF0000",
                font = "tom-thumb",
            ),
        )

    rep = http.get(LASTFM_API, params = {
        "method": "user.getrecenttracks",
        "user": userName,
        "api_key": api_key,
        "format": "json",
        "limit": "1",
    })
    if rep.status_code != 200:
        return render.Root(
            child = render.WrappedText(
                content = "Could not reach Last.fm API.",
                color = "#FF0000",
                font = "tom-thumb",
            ),
        )

    tracks = rep.json().get("recenttracks", {}).get("track", [])
    if not tracks:
        return render.Root(child = render.Text("No recent tracks", font = "5x8"))
    track = tracks[0]

    image_url = largest_image_url(track.get("image"))

    # Last.fm leaves recent-track art blank when a scrobble has no linked album;
    # the track's own album usually still has art.
    if not image_url:
        info = http.get(LASTFM_API, params = {
            "method": "track.getInfo",
            "artist": track["artist"]["#text"],
            "track": track["name"],
            "api_key": api_key,
            "format": "json",
            "autocorrect": "1",
        })
        if info.status_code == 200:
            image_url = largest_image_url(info.json().get("track", {}).get("album", {}).get("image"))

    img = http.get(image_url) if image_url.startswith(ART_HOSTS) else None

    # no art anywhere: a dark box keeps the text readable
    if img == None or img.status_code != 200:
        albumWidget = render.Box(color = "#222", height = 32, width = 32)
    else:
        albumWidget = render.Image(src = img.body(), height = 32, width = 32)

    now = ""
    if clockShown:
        now = time.now()

    return renderIt(now, albumWidget, track)

def renderIt(now, albumWidget, track):
    return render.Root(
        child = render.Stack(
            children = [
                render.Padding(
                    pad = (42, 1, 0, 0),
                    child = render.Text(
                        content = now.format("3:04") if now else "",
                        font = "tom-thumb",
                        color = "#777",
                    ),
                ),
                render.Padding(
                    pad = (0, 0, 0, 0),
                    child = albumWidget,
                ),
                render.Box(
                    color = "#00FF0000",
                    child = render.Padding(
                        pad = (0, 0, 0, 0),
                        color = "#FF000000",
                        child = render.Column(
                            cross_align = "end",
                            main_align = "start",
                            expanded = False,
                            children = [
                                render.Box(
                                    color = "#0000FF00",
                                    height = 6,
                                ),
                                render.Padding(
                                    pad = (1, 1, 0, 0),
                                    color = "#11111199",
                                    child = render.WrappedText("%s" % track["name"], font = "tom-thumb", color = "#FFFFFF"),
                                ),
                                render.Padding(
                                    pad = (1, 1, 0, 0),
                                    color = "#11111199",
                                    child = render.WrappedText("%s" % track["artist"]["#text"], font = "tom-thumb", color = "#FFF"),
                                ),
                            ],
                        ),
                    ),
                ),
            ],
        ),
    )

def demoMode():
    now = time.now()

    albumWidget = render.Image(src = DEMOICON, height = 32, width = 32)
    track = {}
    track["name"] = "Come Together"
    artist = {}
    artist["#text"] = "The Beatles"
    track["artist"] = artist

    return renderIt(now, albumWidget, track)

def get_schema():
    return schema.Schema(
        version = "1",
        fields = [
            schema.Text(
                id = "lastFmUser",
                name = "Last.fm Username",
                desc = "Name of the Last.fm user to view.",
                icon = "user",
                default = "DemoUser",
            ),
            schema.Text(
                id = "lastApiKey",
                name = "Last.fm API Key",
                desc = "Get from Last.fm, used to authenticate.",
                icon = "key",
                default = "DemoKey",
                secret = True,
            ),
            schema.Toggle(
                id = "showClock",
                name = "Show Clock?",
                icon = "clock",
                desc = "Displays a clock showing the local time.",
            ),
        ],
    )
