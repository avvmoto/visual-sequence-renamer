"""リネームコアロジックの簡易テスト。"""

from pathlib import Path

from app.core.rename import (
    perform_rename_in_place,
    perform_undo_rename,
    stem_without_leading_index_prefix,
    target_basename,
)


def test_target_basename_padding() -> None:
    """連番の桁とファイル名形式。"""
    src = Path("x") / "photo.jpg"
    assert target_basename(1, 5, src) == "001_photo.jpg"
    assert target_basename(12, 100, src) == "012_photo.jpg"
    assert target_basename(12, 1000, src) == "0012_photo.jpg"


def test_stem_strip_and_target_with_option() -> None:
    """先頭連番除去とリネーム後のベース名。"""
    assert stem_without_leading_index_prefix("001_photo") == "photo"
    assert stem_without_leading_index_prefix("001_002_photo") == "photo"
    assert stem_without_leading_index_prefix("12_photo") == "12_photo"
    renamed = Path("x") / "001_photo.jpg"
    assert target_basename(1, 3, renamed, strip_leading_index_prefix=True) == "001_photo.jpg"


def test_rename_in_place_and_undo(tmp_path: Path) -> None:
    """同一フォルダでリネームし、元に戻せること。"""
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("xa", encoding="utf-8")
    b.write_text("xb", encoding="utf-8")

    pairs = perform_rename_in_place([a, b])
    assert len(pairs) == 2
    assert (tmp_path / "001_a.txt").read_text(encoding="utf-8") == "xa"
    assert (tmp_path / "002_b.txt").read_text(encoding="utf-8") == "xb"
    assert not a.exists()
    assert not b.exists()

    perform_undo_rename(pairs)
    assert a.read_text(encoding="utf-8") == "xa"
    assert b.read_text(encoding="utf-8") == "xb"
    assert not (tmp_path / "001_a.txt").exists()


def test_repeat_rename_strips_accumulated_prefix(tmp_path: Path) -> None:
    """除去オンで、既に 001_ が付いたファイルを再度リネームしても連番が積み上がらない。"""
    p = tmp_path / "001_photo.jpg"
    p.write_bytes(b"x")
    pairs = perform_rename_in_place([p], strip_leading_index_prefix=True)
    dst, _orig = pairs[0]
    assert dst.name == "001_photo.jpg"
    assert dst.name != "001_001_photo.jpg"
    assert dst.read_bytes() == b"x"
