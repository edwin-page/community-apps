package main

// Apps with "feed": "source" derive every logo URL from team tables in their
// own source: a team a feed returns either maps through those tables to one of
// the URLs below or gets no logo URL at all. Enumerating the tables therefore
// covers every team any feed date can return. Each rule mirrors the app's own
// URL logic; sizes are layout_sizes times scales for every URL.

import (
	"bytes"
	"fmt"
	"image"
	"regexp"
	"sort"
	"strings"
)

// sourceString reads a top-level `NAME = "value"` string constant.
func sourceString(source, name string) (string, error) {
	m := regexp.MustCompile(`(?m)^` + name + ` = "([^"]*)"$`).FindStringSubmatch(source)
	if m == nil {
		return "", fmt.Errorf("no string constant %s", name)
	}
	return m[1], nil
}

// sourceBlock returns the body of a top-level `NAME = {` or `NAME = [` literal.
func sourceBlock(source, name string) (string, error) {
	m := regexp.MustCompile(`(?ms)^` + name + ` = [\[{](.*?)^[\]}]`).FindStringSubmatch(source)
	if m == nil {
		return "", fmt.Errorf("no table %s", name)
	}
	return m[1], nil
}

func stringMap(table map[string]any) map[string]string {
	out := map[string]string{}
	for k, v := range table {
		if s, ok := v.(string); ok {
			out[k] = s
		}
	}
	return out
}

// sourceLogos returns URL -> teams drawing it, for the app's rule.
func sourceLogos(rule, source string) (map[string][]string, error) {
	out := map[string][]string{}
	add := func(url, team string) {
		for _, t := range out[url] {
			if t == team {
				return
			}
		}
		out[url] = append(out[url], team)
	}
	switch rule {
	case "mlb_game": // MLB Game: logo_url_for(code, espn_logo_url)
		altTable, err := sourceTable(source, "ALT_LOGO")
		if err != nil {
			return nil, err
		}
		keyTable, err := sourceTable(source, "TEAM_LOGO_KEY")
		if err != nil {
			return nil, err
		}
		meta, err := sourceTable(source, "ESPN_TEAM_META")
		if err != nil {
			return nil, err
		}
		if len(keyTable) == 0 || len(meta) == 0 {
			return nil, fmt.Errorf("mlb_game: missing TEAM_LOGO_KEY or ESPN_TEAM_META")
		}
		alt, keys := stringMap(altTable), stringMap(keyTable)
		// Codes come from the feed's abbreviation or TEAM_BY_ID, the Team Focus
		// option (no-game screen), and are looked up in the tables above.
		codes := map[string]bool{}
		for _, table := range []map[string]any{altTable, keyTable, meta} {
			for code := range table {
				codes[code] = true
			}
		}
		byID, err := sourceBlock(source, "TEAM_BY_ID")
		if err != nil {
			return nil, err
		}
		for _, m := range regexp.MustCompile(`(?m)^\s*\d+: "(\w+)",`).FindAllStringSubmatch(byID, -1) {
			codes[m[1]] = true
		}
		options, err := sourceBlock(source, "teamOptions")
		if err != nil {
			return nil, err
		}
		for _, m := range regexp.MustCompile(`value = "(\w+)"`).FindAllStringSubmatch(options, -1) {
			codes[m[1]] = true
		}
		urlFor := func(code, espn string) string {
			if url, ok := alt[code]; ok {
				return url
			}
			if espn != "" {
				url := strings.ReplaceAll(espn, "500/scoreboard", "500-dark/scoreboard")
				url = strings.ReplaceAll(url, "https://a.espncdn.com/", "https://a.espncdn.com/combiner/i?img=")
				if !strings.Contains(url, "&h=") && !strings.Contains(url, "&w=") {
					url += "&h=50&w=50"
				}
				return url
			}
			if key, ok := keys[code]; ok {
				return "https://a.espncdn.com/i/teamlogos/mlb/500-dark/" + key + ".png"
			}
			return ""
		}
		for code := range codes {
			espns := []string{""}
			if m, ok := meta[code].(map[string]any); ok {
				if logo, ok := m["logo"].(string); ok && logo != "" {
					espns = append(espns, logo)
				}
			}
			for _, espn := range espns {
				if url := urlFor(code, espn); url != "" {
					add(url, code)
				}
			}
		}
	case "nhl_live": // NHL Live: get_team_logo(teamId)
		base, err := sourceString(source, "BASE_IMAGE_URL")
		if err != nil {
			return nil, err
		}
		teams, err := sourceBlock(source, "TEAMS_LIST")
		if err != nil {
			return nil, err
		}
		re := regexp.MustCompile(`(?m)^\s*\d+: \{"name": "[^"]*", "abbreviation": "(\w+)"(?:, "abbr_fix": "(\w+)")?\},`)
		for _, m := range re.FindAllStringSubmatch(teams, -1) {
			abbr := m[1]
			if m[2] != "" {
				abbr = m[2]
			}
			add(strings.Replace(base, "{}", abbr, 1), m[1])
		}
	case "mlb_next_games": // MLB Next Games: TEAMS[*].image
		bases := map[string]string{}
		for _, name := range []string{"IMAGE_BASE", "IMAGE_BASE_DARK"} {
			value, err := sourceString(source, name)
			if err != nil {
				return nil, err
			}
			bases[name] = value
		}
		teams, err := sourceBlock(source, "TEAMS")
		if err != nil {
			return nil, err
		}
		re := regexp.MustCompile(`(?m)^\s*\{"name": "[^"]*", "id": \d+, "nick": "(\w+)", "image": "%s([\w.]+)" % (IMAGE_BASE(?:_DARK)?)\},`)
		for _, m := range re.FindAllStringSubmatch(teams, -1) {
			add(bases[m[3]]+m[2], m[1])
		}
	case "mlbliveticker": // MLB Live Ticker: logo(team_id, size)
		pattern, err := sourceString(source, "LOGO_URL")
		if err != nil {
			return nil, err
		}
		slugs, err := sourceTable(source, "ESPN_SLUGS")
		if err != nil {
			return nil, err
		}
		teams, err := sourceTable(source, "TEAMS")
		if err != nil {
			return nil, err
		}
		for id, slug := range stringMap(slugs) {
			team := id
			if info, ok := teams[id].([]any); ok && len(info) > 0 {
				team, _ = info[0].(string)
			}
			add(strings.Replace(pattern, "%s", slug, 1), team)
		}
	default:
		return nil, fmt.Errorf("unknown source rule %q", rule)
	}
	if len(out) == 0 {
		return nil, fmt.Errorf("%s: no logo URLs found in source", rule)
	}
	for _, teams := range out {
		sort.Strings(teams)
	}
	return out, nil
}

// sourceUses downloads every URL from sourceLogos; URLs that do not return a
// decodable image stay on the network path, exactly as before.
func sourceUses(cfg appConfig, source string) (map[string]*logoUse, []string, error) {
	logos, err := sourceLogos(cfg.Rule, source)
	if err != nil {
		return nil, nil, err
	}
	var sizes []int
	for _, scale := range cfg.Scales {
		for _, size := range cfg.LayoutSizes {
			sizes = append(sizes, size*scale)
		}
	}
	uses := map[string]*logoUse{}
	var unbundled []string
	for _, url := range sortedKeys(logos) {
		d := fetch(url)
		if d.err != nil || d.status != 200 {
			unbundled = append(unbundled, fmt.Sprintf("%s %s (status %d %v)", strings.Join(logos[url], ","), url, d.status, d.err))
			continue
		}
		if _, _, err := image.DecodeConfig(bytes.NewReader(d.body)); err != nil {
			unbundled = append(unbundled, fmt.Sprintf("%s %s (%v)", strings.Join(logos[url], ","), url, err))
			continue
		}
		u := &logoUse{teams: map[string]bool{}, sizes: map[int]bool{}}
		for _, team := range logos[url] {
			u.teams[team] = true
		}
		for _, size := range sizes {
			u.sizes[size] = true
		}
		uses[url] = u
	}
	return uses, unbundled, nil
}
