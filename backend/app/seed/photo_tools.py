"""One-off developer tool that builds the bundled demo photo set from Wikimedia Commons.

    python -m app.seed.photo_tools curate    # search Commons, write photo_sources.json
    python -m app.seed.photo_tools download  # fetch, resize to WebP, write CREDITS.md

Only photos under CC BY, CC BY-SA, CC0 or public-domain terms are kept, and every photo's author
and license is recorded so the attribution those licenses require can be published. The results
are committed to the repository, so the running app never needs the network.
"""

import io
import json
import re
import sys
import time
from html import unescape
from pathlib import Path

import httpx
from PIL import Image

SEED_DIR = Path(__file__).resolve().parent
MEDIA_ROOT = SEED_DIR.parent.parent / "media" / "seed"
MANIFEST = SEED_DIR / "photo_sources.json"
API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = (
    "AirbnbCloneDemo/1.0 (https://github.com/dev-harshvats/Airbnb_clone; demo photo curation) httpx"
)

FULL_WIDTH, CARD_WIDTH, QUALITY = 1440, 720, 80
PER_THEME = 10

# theme -> Commons search phrases, in order of preference
THEMES: dict[str, list[str]] = {
    "beach": [
        "Goa beach palm",
        "Palolem beach",
        "Gokarna Om beach",
        "Varkala beach cliff",
        "Pondicherry beach",
    ],
    "hills": [
        "Manali valley Himachal",
        "Shimla Himachal view",
        "Darjeeling Himalaya",
        "Munnar tea plantation",
        "Ooty Nilgiri lake",
    ],
    "estate": [
        "Coorg coffee plantation",
        "Kodagu landscape",
        "Wayanad plantation",
        "Chikmagalur estate",
    ],
    "heritage": [
        "Udaipur City Palace",
        "Jaipur Amber Fort",
        "Jaisalmer fort haveli",
        "Rajasthan haveli courtyard",
    ],
    "desert": ["Jaisalmer Sam sand dunes", "Thar desert camp", "Rajasthan desert camel sunset"],
    "backwaters": ["Kerala houseboat Alleppey", "Kerala backwaters boat", "Alappuzha backwaters"],
    "ladakh": [
        "Leh Ladakh landscape",
        "Pangong Tso lake",
        "Thiksey monastery Ladakh",
        "Nubra valley",
    ],
    "spiritual": ["Rishikesh Ganges", "Varanasi ghats Ganges", "Laxman Jhula Rishikesh"],
    "city": [
        "Mumbai Marine Drive",
        "Bangalore skyline",
        "Fort Kochi Chinese fishing nets",
        "Mumbai Gateway of India",
    ],
    "pool": [
        "resort swimming pool India",
        "villa swimming pool Goa",
        "luxury resort pool India",
        "hotel pool Kerala",
    ],
    "interior": [
        "hotel room interior India",
        "resort bedroom India",
        "heritage hotel room Rajasthan",
        "homestay room India",
        "resort room Goa",
        "luxury hotel suite India",
        "Kerala resort room",
    ],
    "cabin": [
        "wooden cottage Himachal",
        "treehouse Wayanad",
        "tent camp Himalaya",
        "mud house homestay India",
        "Manali wooden cottage",
        "Himachal homestay",
        "Munnar resort cottage",
        "bamboo cottage Kerala",
        "glamping tent India",
        "Coorg homestay",
    ],
}

_ALLOWED_LICENSE = re.compile(r"^(CC BY(-SA)? [0-9.]+|CC0.*|Public domain.*|PD.*)$", re.I)
_REJECT_TITLE = re.compile(
    r"\b(map|logo|flag|stamp|poster|painting|drawing|diagram|coin|emblem|sketch|scan|book|"
    r"newspaper|passport|ticket|certificate|portrait|wedding|protest|rally|accident|police|army)\b",
    re.I,
)


# Files the search surfaced that are off-theme (vehicles, animals, ballrooms, people as the subject).
_EXCLUDE_SUBSTRINGS = (
    "toy train",
    "railway carriages",
    "sheep",
    "white horses",
    "yatch",
    "politely declined",
    "adventure park",
    "tuk tuk",
    "baedeker",
    "flower buds",
    "timeless bond of rishikesh and the ganges 07",
    "rock beach (puducherry beach) 3",
    "cooking on the flame",
    "preparing bread",
    "tsogskor",
    "ball room",
    "shashi kapoor",
    "people and beach",
    "paharganj",
    "taj palace hotel",
    "street views from coorg",
)


def _strip_html(value: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", value or "")).strip()


def _search(client: httpx.Client, phrase: str) -> list[dict]:
    response = client.get(
        API,
        params={
            "action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
            "gsrsearch": f"{phrase} filetype:bitmap", "gsrlimit": 40, "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata", "iiurlwidth": FULL_WIDTH,
            "iiextmetadatafilter": "LicenseShortName|Artist",
        },
    )  # fmt: skip
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    return sorted(pages.values(), key=lambda p: p.get("index", 0))


def _usable(page: dict) -> dict | None:
    info = (page.get("imageinfo") or [{}])[0]
    meta = info.get("extmetadata", {})
    license_name = _strip_html(meta.get("LicenseShortName", {}).get("value", ""))
    width, height = info.get("width", 0), info.get("height", 0)
    title = page["title"].removeprefix("File:")
    if (
        not info.get("thumburl")
        or info.get("mime") not in {"image/jpeg", "image/png"}
        or not _ALLOWED_LICENSE.match(license_name)
        or _REJECT_TITLE.search(title)
        or any(bad in title.lower() for bad in _EXCLUDE_SUBSTRINGS)
        or width < 1800
        or height < 1100
        or not 1.3 <= width / height <= 1.9
    ):
        return None
    return {
        "title": title,
        "thumb_url": info["thumburl"],
        "page_url": info["descriptionurl"],
        "author": _strip_html(meta.get("Artist", {}).get("value", "")) or "Unknown",
        "license": license_name,
    }


def curate() -> None:
    manifest: dict[str, list[dict]] = {}
    seen: set[str] = set()
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30) as client:
        for theme, phrases in THEMES.items():
            picks: list[dict] = []
            per_phrase = [[] for _ in phrases]
            for i, phrase in enumerate(phrases):
                for page in _search(client, phrase):
                    candidate = _usable(page)
                    if candidate and candidate["title"] not in seen:
                        per_phrase[i].append(candidate)
                time.sleep(0.5)
            # round-robin across the phrases so one search term cannot dominate a theme
            for rank in range(40):
                for candidates in per_phrase:
                    if rank < len(candidates) and len(picks) < PER_THEME:
                        pick = candidates[rank]
                        if pick["title"] not in seen:
                            seen.add(pick["title"])
                            picks.append(pick)
            manifest[theme] = picks
            print(f"{theme:11} {len(picks):2} photos")
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _render(image: Image.Image, width: int) -> bytes:
    resized = (
        image
        if image.width <= width
        else image.resize((width, round(image.height * width / image.width)))
    )
    out = io.BytesIO()
    resized.save(out, format="WEBP", quality=QUALITY)
    return out.getvalue()


def download() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    credits = [
        "# Photo credits",
        "",
        "The demo photos in this folder come from Wikimedia Commons and are used under the licenses",
        "listed below (CC BY, CC BY-SA, CC0 or public domain). They were resized and converted to",
        "WebP. Each entry links to the original file page with its full attribution details.",
        "",
        "| File | Photo | Author | License |",
        "|---|---|---|---|",
    ]
    total = 0
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, timeout=60, follow_redirects=True
    ) as client:
        for theme, photos in manifest.items():
            folder = MEDIA_ROOT / "photos" / theme
            folder.mkdir(parents=True, exist_ok=True)
            for number, photo in enumerate(photos, start=1):
                full_path, card_path = (
                    folder / f"{number:02d}.webp",
                    folder / f"{number:02d}_card.webp",
                )
                if not full_path.exists():
                    for attempt in range(4):  # Commons asks clients to back off when rate limited
                        response = client.get(photo["thumb_url"])
                        if response.status_code == 429:
                            time.sleep(5 * (attempt + 1))
                            continue
                        response.raise_for_status()
                        break
                    image = Image.open(io.BytesIO(response.content)).convert("RGB")
                    full_path.write_bytes(_render(image, FULL_WIDTH))
                    card_path.write_bytes(_render(image, CARD_WIDTH))
                    time.sleep(1.0)
                total += full_path.stat().st_size + card_path.stat().st_size
                author = photo["author"].replace("|", "/")[:60]
                credits.append(
                    f"| photos/{theme}/{number:02d}.webp | [{photo['title'][:60]}]({photo['page_url']}) "
                    f"| {author} | {photo['license']} |"
                )
            print(f"{theme:11} {len(photos):2} photos")
    (MEDIA_ROOT / "CREDITS.md").write_text("\n".join(credits) + "\n", encoding="utf-8")
    print(f"total {total / 1_048_576:.1f} MB")


if __name__ == "__main__":
    {"curate": curate, "download": download}.get(
        sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__)
    )()
