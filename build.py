#!/usr/bin/env python3
"""Build index.html for fullgridreview.com from the design file Main.dc.html.

Usage: python3 build.py   (run from this folder; reads Main.dc.html, writes index.html)

The design file uses {{holes}} and <sc-for> loops filled from the renderVals()
data in its script block. This script evaluates that data (standings rows and
episode cards are plain literals), expands the loops, swaps the canvas logo
blob for logo.webp, and adds the page head, favicon and newsletter signup.
"""
import re, json, html, pathlib

HERE = pathlib.Path(__file__).parent
src = (HERE / "Main.dc.html").read_text(encoding="utf-8")

# ---- data from the script block ----
props = json.loads(re.search(r"data-props='(.*?)'", src, re.S).group(1))
accent = props["accent"]["default"]
script = re.search(r"renderVals\(\)\s*\{(.*)\n\s*\}\n\s*\}\n</script>", src, re.S).group(1)
m = re.search(r"var accent = this\.props\.accent \?\? '([^']+)'", script)
if m: accent = m.group(1)

raw_txt = re.search(r"var raw = (\[.*?\]);", script, re.S).group(1)
raw = json.loads(raw_txt.replace("'", '"'))
lead = raw[0][2]
standings = []
for i, (name, team, pts) in enumerate(raw):
    pct = round(pts / lead * 1000) / 10
    standings.append({"pos": i + 1, "name": name, "team": team, "pts": pts,
        "bar": f"height: 100%; width: {pct}%; background: {accent if i == 0 else '#5A6470'}; border-radius: 4px"})

w = "https://www.youtube.com/watch?v="
ep_txt = re.search(r"var episodes = (\[.*?\]);", script, re.S).group(1)
episodes = []
for obj in re.findall(r"\{(.*?)\}", ep_txt, re.S):
    ep = {}
    for k, v in re.findall(r"(\w+):\s*((?:w \+ )?'(?:[^'\\]|\\.)*')", obj):
        val = re.search(r"'((?:[^'\\]|\\.)*)'", v).group(1).replace("\\'", "'")
        ep[k] = (w + val) if v.startswith("w +") else val
    episodes.append(ep)

data = {"accent": accent, "standings": standings, "episodes": episodes}

def lookup(path, scope):
    cur = scope
    for part in path.split("."):
        cur = cur[part]
    return cur

def fill(text, scope):
    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", lambda mm: html.escape(str(lookup(mm.group(1), scope)), quote=True), text)

body = re.search(r"<x-dc>(.*)</x-dc>", src, re.S).group(1)
helmet = re.search(r"<helmet>(.*?)</helmet>", body, re.S).group(1)
body = re.sub(r"<helmet>.*?</helmet>", "", body, flags=re.S)

def expand(mm):
    lst, var, inner = mm.group(1), mm.group(2), mm.group(3)
    return "".join(fill(inner, {**data, var: item}) for item in lookup(lst, data))
body = re.sub(r'<sc-for list="\{\{(\w+)\}\}" as="(\w+)"[^>]*>(.*?)</sc-for>', expand, body, flags=re.S)
body = fill(body, data)
body = re.sub(r'/_blob/[0-9a-f]{32}', 'logo.webp', body)

# ---- newsletter signup (Beehiiv) ----
SIGNUP = '''
<section id="newsletter" style="padding: 96px 24px; border-bottom: 1px solid #1F242B">
<div style="max-width: 760px; margin: 0 auto; text-align: center">
<p style="margin: 0 0 12px; font-family: 'JetBrains Mono', monospace; font-size: 13px; letter-spacing: 0.14em; text-transform: uppercase; color: ACCENT">FGR Weekly · Free newsletter</p>
<h2 style="margin: 0; font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: clamp(32px, 4.5vw, 48px); line-height: 1.1">Every race in five to eight minutes, in your inbox.</h2>
<p style="margin: 18px auto 0; max-width: 560px; color: #B4BDC7">One issue per Grand Prix and weekly through the off-season: the result, why it happened, and the title math.</p>
<div style="margin-top: 32px; display: flex; justify-content: center">
<script async src="https://subscribe-forms.beehiiv.com/v3/loader.js" data-beehiiv-form="ea3256cf-968f-4e67-a632-0a919e64de4e"></script>
</div>
<p style="margin: 28px 0 0"><a href="newsletter/" style="font-family: 'JetBrains Mono', monospace; font-size: 14px; letter-spacing: 0.06em; min-height: 44px; display: inline-flex; align-items: center">READ PAST ISSUES →</a></p>
</div>
</section>
'''.replace("ACCENT", accent)
body = body.replace('<section id="about"', SIGNUP + '\n<section id="about"', 1)
body = body.replace('<a href="#about" style="color: #B4BDC7">About</a>',
    '<a href="#newsletter" style="color: #B4BDC7">Newsletter</a>\n<a href="#about" style="color: #B4BDC7">About</a>', 1)

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Full Grid Review | F1 Race Recaps Every Monday</title>
<meta name="description" content="One Formula 1 recap per Grand Prix, out the Monday after: what happened, why it happened, and what it means for the title fight.">
<link rel="canonical" href="https://fullgridreview.com/">
<meta property="og:type" content="website">
<meta property="og:url" content="https://fullgridreview.com/">
<meta property="og:title" content="The Full Grid Review">
<meta property="og:description" content="F1 race recaps every Monday: what happened, why it happened, and what it means for the title fight.">
<meta property="og:image" content="https://fullgridreview.com/og-image.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="favicon.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="theme-color" content="#0D0F12">
{helmet.strip()}
<style>html{{scroll-behavior:smooth}}img{{max-width:100%}}</style>
</head>
<body>
{body.strip()}
<script type="text/javascript" async src="https://subscribe-forms.beehiiv.com/attribution.js"></script>
</body>
</html>
'''
(HERE / "index.html").write_text(page, encoding="utf-8")
print("index.html written:", len(page), "bytes;", len(standings), "standings rows,", len(episodes), "episodes")
