"""リネームコアロジックの簡易テスト。"""

from pathlib import Path

from app.core.rename import perform_rename_in_place, perform_undo_rename, target_basename


def test_target_basename_padding() -> None:
    """連番の桁とファイル名形式。"""
    src = Path("x") / "photo.jpg"
    assert target_basename(1, 5, src) == "001_photo.jpg"
    assert target_basename(12, 100, src) == "012_photo.jpg"
    assert target_basename(12, 1000, src) == "0012_photo.jpg"


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
