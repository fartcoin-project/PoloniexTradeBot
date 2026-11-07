"""Generate Windows icons and Inno Setup wizard art from project PNGs."""

from __future__ import annotations

from pathlib import Path

ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
WIZARD_SIZE = (164, 314)


def project_root_from() -> Path:
    return Path(__file__).resolve().parent.parent


def default_paths(root: Path | None = None) -> dict[str, Path]:
    project_root = Path(root) if root is not None else project_root_from()
    assets = project_root / "installer" / "assets"
    return {
        "icon_png": project_root / "icon.png",
        "art_png": project_root / "art.png",
        "icon_ico": assets / "icon.ico",
        "art_ico": assets / "art.ico",
        "wizard_bmp": assets / "wizard.bmp",
    }


def png_to_ico(png_path: Path, ico_path: Path, sizes: tuple[int, ...] = ICO_SIZES) -> Path:
    from PIL import Image

    png_path = Path(png_path)
    ico_path = Path(ico_path)
    ico_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(png_path) as image:
        rgba = image.convert("RGBA")
        # Pillow builds each requested size from this image when saving ICO.
        largest = max(sizes)
        master = rgba.resize((largest, largest), Image.Resampling.LANCZOS)
        master.save(ico_path, format="ICO", sizes=[(size, size) for size in sizes])
    return ico_path


def png_to_wizard_bmp(
    png_path: Path,
    bmp_path: Path,
    size: tuple[int, int] = WIZARD_SIZE,
    background=(0, 0, 0),
) -> Path:
    """Place square art centered on a tall black bitmap for Inno WizardImageFile."""
    from PIL import Image

    png_path = Path(png_path)
    bmp_path = Path(bmp_path)
    bmp_path.parent.mkdir(parents=True, exist_ok=True)

    width, height = size
    canvas = Image.new("RGB", (width, height), background)
    with Image.open(png_path) as image:
        rgba = image.convert("RGBA")
        side = min(width, height) - 16
        if side < 1:
            side = min(width, height)
        art = rgba.resize((side, side), Image.Resampling.LANCZOS)
        x = (width - side) // 2
        y = (height - side) // 2
        canvas.paste(art, (x, y), art)
    canvas.save(bmp_path, format="BMP")
    return bmp_path


def generate_all(root: Path | None = None) -> dict[str, Path]:
    paths = default_paths(root)
    png_to_ico(paths["icon_png"], paths["icon_ico"])
    png_to_ico(paths["art_png"], paths["art_ico"])
    png_to_wizard_bmp(paths["art_png"], paths["wizard_bmp"])
    return paths


def main() -> int:
    paths = generate_all()
    for key, path in paths.items():
        if key.endswith(("_ico", "_bmp")):
            print(f"{key}: {path} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
