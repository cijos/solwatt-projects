#!/usr/bin/env python3
"""links.txt -> site/places.json: turn Google Maps links into map points (name, lat, lng, url).

Short share links (maps.app.goo.gl / goo.gl/maps) are followed to the full Google Maps address once and cached
in scripts/cache.json. Lines that can't be turned into a point are reported, not fatal.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINKS = os.path.join(ROOT, "links.txt")
OUT = os.path.join(ROOT, "site", "places.json")
CACHE = os.path.join(ROOT, "scripts", "cache.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
NUM = r"(-?\d{1,3}\.\d+)"


def load_cache():
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def expand(url, cache):
    """Follow redirects of short links to the full Google Maps URL."""
    host = urllib.parse.urlparse(url).netloc.lower()
    if not (host.endswith("goo.gl") or host.endswith("app.goo.gl") or host == "g.co"):
        return url
    if url in cache:
        return cache[url]
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=20) as r:
        final = r.geturl()
        if "consent.google" in final:   # cookie-consent page: the real address is in ?continue=
            final = urllib.parse.parse_qs(urllib.parse.urlparse(final).query).get("continue", [final])[0]
    cache[url] = final
    return final


def coords(url):
    u = urllib.parse.unquote(url)
    for pat in (r"!3d" + NUM + r"!4d" + NUM, r"@" + NUM + r"," + NUM):
        m = re.search(pat, u)
        if m:
            return float(m.group(1)), float(m.group(2))
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    for key in ("q", "query", "ll", "destination", "center"):
        for v in q.get(key, []):
            m = re.fullmatch(r"\s*" + NUM + r"\s*,\s*" + NUM + r"\s*", v)
            if m:
                return float(m.group(1)), float(m.group(2))
    return None


def name_from(url):
    m = re.search(r"/maps/place/([^/@?]+)", url)
    if m:
        n = urllib.parse.unquote_plus(m.group(1)).strip()
        if not re.fullmatch(r"""[-\d.,°'"\sNSEW]+""", n):   # a dropped pin is named like 10°31'48.2"N 76°15'01.1"E
            return n
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("q", [""])[0]
    if q and not re.fullmatch(r"[-\d.,\s]+", q):
        return q.strip()
    return None


def main():
    cache = load_cache()
    places, problems = [], []
    with open(LINKS, encoding="utf-8") as f:
        lines = [l.strip() for l in f]
    for n, line in enumerate(lines, 1):
        if not line or line.startswith("#"):
            continue
        name, _, link = line.rpartition("|") if "|" in line else ("", "", line)
        name, link = name.strip(), link.strip()
        if not link.startswith("http"):
            problems.append(f"line {n}: not a link: {line}")
            continue
        try:
            full = expand(link, cache)
        except Exception as e:  # noqa: BLE001 - report and carry on
            problems.append(f"line {n}: could not open the short link ({e}) - paste the full Google Maps link instead")
            continue
        c = coords(full)
        if not c:
            problems.append(f"line {n}: no location found in the link - open it in Google Maps and copy the full address bar link")
            continue
        lat, lng = c
        if not (6 <= lat <= 37 and 68 <= lng <= 98):
            problems.append(f"line {n}: {lat},{lng} is outside India - check the link")
            continue
        places.append({"name": name or name_from(full) or f"Place {len(places) + 1}", "lat": round(lat, 6),
                       "lng": round(lng, 6), "url": link})
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(places, f, ensure_ascii=False, indent=1)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=1, sort_keys=True)
    print(f"{len(places)} places written to site/places.json")
    for p in problems:
        print("WARNING " + p)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"### Map: {len(places)} places\n" + "".join(f"- ⚠️ {p}\n" for p in problems))
    return 0


if __name__ == "__main__":
    sys.exit(main())
