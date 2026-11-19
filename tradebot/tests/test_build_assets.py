"""Tests for installer/app icon asset generation."""

from pathlib import Path

import pytest

from build_assets import generate_all, png_to_ico, png_to_wizard_bmp, WIZARD_SIZE


pytest.importorskip("PIL")


@pytest.fixture
def sample_png(tmp_path):
    from PIL import Image

    path = tmp_path / "sample.png"
    Image.new("RGBA", (64, 64), (0, 255, 128, 255)).save(path)
    return path


def test_png_to_ico_writes_file(sample_png, tmp_path):
    out = tmp_path / "out.ico"
    result = png_to_ico(sample_png, out, sizes=(16, 32, 48))
    assert result == out
    assert out.is_file()
    assert out.stat().st_size > 0


def test_png_to_wizard_bmp_size(sample_png, tmp_path):
    from PIL import Image

    out = tmp_path / "wizard.bmp"
    png_to_wizard_bmp(sample_png, out)
    with Image.open(out) as image:
        assert image.size == WIZARD_SIZE
        assert image.mode in ("RGB", "RGBA")


def test_generate_all_uses_project_pngs(tmp_path):
    from PIL import Image

    root = tmp_path / "project"
    root.mkdir()
    Image.new("RGBA", (128, 128), (10, 20, 30, 255)).save(root / "icon.png")
    Image.new("RGBA", (128, 128), (40, 50, 60, 255)).save(root / "art.png")

    paths = generate_all(root)

    assert paths["icon_ico"].is_file()
    assert paths["art_ico"].is_file()
    assert paths["wizard_bmp"].is_file()
    assert paths["icon_ico"].parent == root / "installer" / "assets"
