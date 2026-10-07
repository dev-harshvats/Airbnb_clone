"""Initials avatars, generated locally so the demo ships no photos of real people."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 256
COLOURS = [
    (255, 56, 92), (0, 138, 149), (255, 180, 0), (113, 71, 168), (34, 34, 34),
    (230, 81, 0), (46, 125, 50), (21, 101, 192), (173, 20, 87), (93, 64, 55),
]  # fmt: skip


def write_avatar(path: Path, initials: str, colour: tuple[int, int, int]) -> None:
    image = Image.new("RGB", (SIZE, SIZE), colour)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=110)
    left, top, right, bottom = draw.textbbox((0, 0), initials, font=font)
    draw.text(
        ((SIZE - (right - left)) / 2 - left, (SIZE - (bottom - top)) / 2 - top),
        initials,
        fill="white",
        font=font,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="WEBP", quality=85)


def avatar_url_for(index: int, first_name: str, last_name: str, media_dir: Path) -> str:
    """Create `media/seed/avatars/<n>.webp` and return the URL it is served from."""
    file_name = f"{index + 1:02d}.webp"
    write_avatar(
        Path(media_dir) / "seed" / "avatars" / file_name,
        f"{first_name[0]}{last_name[0]}",
        COLOURS[index % len(COLOURS)],
    )
    return f"/media/seed/avatars/{file_name}"
