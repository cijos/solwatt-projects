# Kerala Places Map

Google Maps links → red pins on a zoomable map: **https://cijos.github.io/kerala-map/**

Map: [Leaflet](https://leafletjs.com) (open source) with [OpenStreetMap](https://www.openstreetmap.org) tiles – no API key.

## Add or remove places
Edit **`links.txt`** (on github.com: open the file → ✏️ → Commit changes). One place per line:
```
Kochi | https://www.google.com/maps/place/Kochi,+Kerala/@9.93,76.26,12z
https://maps.app.goo.gl/AbCdEf123        (short "Share" links work; the name is read from the link)
```
About a minute after saving, the GitHub Action turns the links into points (`site/places.json`) and republishes the
page. If a link can't be read, the Action's summary lists it – open the place in Google Maps on a computer and copy
the full link from the address bar instead.

## Files
- `links.txt` – your list
- `scripts/resolve.py` – reads the links (follows short links, finds the coordinates and name)
- `site/index.html` – the map page
- `.github/workflows/pages.yml` – builds and publishes to GitHub Pages
