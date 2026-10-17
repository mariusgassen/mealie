import colorsys
import hashlib
import io
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

GLYPH_PATH = Path(__file__).parents[2] / "assets" / "icon_glyph.png"

# supersampling factor: shapes are drawn this much larger and scaled down, which smooths the edges
_SCALE = 4


class IconSpec:
    """How one served icon looks: its size and whether the OS (not us) rounds its corners"""

    def __init__(self, size: int, full_bleed: bool = False) -> None:
        self.size = size
        self.full_bleed = full_bleed


# name -> spec. Full-bleed icons fill the whole square (iOS and Android round them), the others are a rounded tile
# on a transparent background, which suits browser tabs and the "any" purpose of the web manifest.
ICONS: dict[str, IconSpec] = {
    "android-chrome-192x192.png": IconSpec(192),
    "android-chrome-512x512.png": IconSpec(512),
    "android-chrome-maskable-192x192.png": IconSpec(192, full_bleed=True),
    "android-chrome-maskable-512x512.png": IconSpec(512, full_bleed=True),
    "apple-touch-icon.png": IconSpec(180, full_bleed=True),
    "mstile-150x150.png": IconSpec(150, full_bleed=True),
    "favicon-16x16.png": IconSpec(16),
    "favicon-32x32.png": IconSpec(32),
    "icon-x64.png": IconSpec(64),
}

ICO_NAME = "favicon.ico"


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _shift_lightness(rgb: tuple[int, int, int], delta: float) -> tuple[int, int, int]:
    h, lightness, s = colorsys.rgb_to_hls(*(channel / 255 for channel in rgb))
    r, g, b = colorsys.hls_to_rgb(h, min(max(lightness + delta, 0), 1), s)
    return round(r * 255), round(g * 255), round(b * 255)


def _luminance(rgb: tuple[int, int, int]) -> float:
    def channel(value: int) -> float:
        c = value / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def readable_on(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    """White, unless the color is light enough that a dark mark is clearly easier to see"""
    return (255, 255, 255) if _luminance(rgb) <= 0.45 else (28, 28, 30)


@lru_cache(maxsize=1)
def _glyph() -> Image.Image:
    return Image.open(GLYPH_PATH).convert("L")


def _gradient(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    column = Image.new("RGB", (1, size))
    for y in range(size):
        t = y / max(size - 1, 1)
        column.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(top, bottom, strict=True)))
    return column.resize((size, size))


def render_icon(spec: IconSpec, primary: str) -> Image.Image:
    """A themed app icon: a soft gradient tile in the primary color with the fork and knife on top"""
    size = spec.size * _SCALE
    base = _hex_to_rgb(primary)

    tile = _gradient(size, _shift_lightness(base, 0.07), _shift_lightness(base, -0.09)).convert("RGBA")

    if not spec.full_bleed:
        mask = Image.new("L", (size, size), 0)
        radius = round(size * 0.225)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
        tile.putalpha(mask)

    glyph = _glyph()
    # full-bleed icons get cropped by the OS, so keep the mark well inside the safe zone
    target = round(size * (0.52 if spec.full_bleed else 0.60))
    ratio = target / max(glyph.size)
    glyph = glyph.resize((max(round(glyph.width * ratio), 1), max(round(glyph.height * ratio), 1)), Image.LANCZOS)
    position = ((size - glyph.width) // 2, (size - glyph.height) // 2)

    glyph_layer = Image.new("L", (size, size), 0)
    glyph_layer.paste(glyph, position)

    # a soft shadow under the mark gives the tile some depth; skipped on tiny sizes where it would just blur
    if spec.size >= 48:
        shadow = ImageChops.offset(glyph_layer, 0, round(size * 0.012)).filter(ImageFilter.GaussianBlur(size * 0.012))
        shadow = shadow.point(lambda value: round(value * 0.28))
        tile.paste(Image.new("RGBA", (size, size), (0, 0, 0, 255)), mask=shadow)

    tile.paste(Image.new("RGBA", (size, size), (*readable_on(base), 255)), mask=glyph_layer)

    return tile.resize((spec.size, spec.size), Image.LANCZOS)


def icon_png(name: str, primary: str) -> bytes | None:
    spec = ICONS.get(name)
    if spec is None:
        return None

    buffer = io.BytesIO()
    render_icon(spec, primary).save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def icon_ico(primary: str) -> bytes:
    buffer = io.BytesIO()
    render_icon(IconSpec(64), primary).save(buffer, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    return buffer.getvalue()


def icon_etag(name: str, primary: str) -> str:
    """Changes when the color or the artwork does, so clients revalidate cheaply instead of re-downloading"""
    artwork = GLYPH_PATH.stat().st_mtime_ns
    return '"' + hashlib.sha256(f"{name}:{primary}:{artwork}".encode()).hexdigest()[:24] + '"'
