"""同一フォルダ内の連番リネームと元に戻し（GUI 非依存）。"""

from __future__ import annotations

import re
import uuid
from pathlib import Path

# 本アプリが付与する連番プレフィックス（3桁以上の数字＋アンダースコア）を stem 先頭から除去する。
_LEADING_INDEX_PREFIX = re.compile(r"^\d{3,}_")


def sequence_width(total: int) -> int:
    """連番の桁数（最低3桁）を返す。

    Args:
        total: ファイル件数。

    Returns:
        ゼロ埋め幅。
    """
    return max(3, len(str(total)))


def stem_without_leading_index_prefix(stem: str) -> str:
    """stem 先頭の「数字3桁以上＋_」を繰り返し取り除く。

    同じフォルダでリネームを繰り返したとき、連番が何重にも付かないようにする。

    Args:
        stem: 拡張子を除いたファイル名。

    Returns:
        除去後の stem。すべて削って空になる場合は元の ``stem`` を返す。
    """
    s = stem
    while True:
        m = _LEADING_INDEX_PREFIX.match(s)
        if not m:
            break
        s = s[m.end() :]
    return s if s else stem


def target_basename(
    index: int,
    total: int,
    source: Path,
    *,
    strip_leading_index_prefix: bool = False,
) -> str:
    """``[連番]_[元のファイル名].[拡張子]`` 形式のファイル名を返す。

    Args:
        index: 1 始まりの連番。
        total: 総件数（桁数決定用）。
        source: 元ファイルパス。
        strip_leading_index_prefix: True のとき、stem 先頭の ``###_`` 形式を除いてから連番を付ける。

    Returns:
        新しいベース名（パス区切りなし）。
    """
    w = sequence_width(total)
    prefix = str(index).zfill(w)
    stem = (
        stem_without_leading_index_prefix(source.stem)
        if strip_leading_index_prefix
        else source.stem
    )
    return f"{prefix}_{stem}{source.suffix}"


def perform_rename_in_place(
    sources: list[Path],
    *,
    strip_leading_index_prefix: bool = False,
) -> list[tuple[Path, Path]]:
    """同一フォルダ内で、表示順に連番名へリネームする。

    一時名を経由して相互上書きを避ける。

    Args:
        sources: 表示順のソースファイル（いずれも同一親ディレクトリ）。
        strip_leading_index_prefix: ``target_basename`` に渡す先頭連番除去フラグ。

    Returns:
        元に戻す用の ``(リネーム後パス, リネーム前パス)`` のリスト（ファイルパスは解決済み）。

    Raises:
        OSError: フォルダ不一致・欠損ファイル・名前衝突・リネーム失敗時。
    """
    if not sources:
        return []

    resolved = [p.expanduser().resolve() for p in sources]
    parent = resolved[0].parent
    for p in resolved:
        if p.parent != parent:
            msg = "すべて同じフォルダ内のファイルである必要があります。"
            raise OSError(msg)
        if not p.is_file():
            msg = f"ファイルが見つかりません: {p}"
            raise OSError(msg)

    total = len(resolved)
    tag = uuid.uuid4().hex[:12]
    staged: list[tuple[Path, Path]] = []

    try:
        for i, src in enumerate(resolved):
            tmp = parent / f".renamer_{tag}_{i:04d}.tmp"
            if tmp.exists():
                msg = f"一時ファイルを作成できません: {tmp}"
                raise OSError(msg)
            src.rename(tmp)
            staged.append((tmp, src))
    except Exception:
        for tmp, orig in reversed(staged):
            if tmp.exists():
                tmp.rename(orig)
        raise

    completed: list[tuple[Path, Path]] = []
    try:
        for i, (tmp, orig) in enumerate(staged):
            dst = parent / target_basename(
                i + 1,
                total,
                orig,
                strip_leading_index_prefix=strip_leading_index_prefix,
            )
            if dst.exists():
                msg = f"既に存在します: {dst.name}"
                raise OSError(msg)
            tmp.rename(dst)
            completed.append((dst, orig))
    except Exception:
        for dst, orig in reversed(completed):
            if dst.exists():
                dst.rename(orig)
        for j in range(len(completed), len(staged)):
            tmp, orig = staged[j]
            if tmp.exists():
                tmp.rename(orig)
        raise

    return completed


def perform_undo_rename(pairs: list[tuple[Path, Path]]) -> None:
    """``perform_rename_in_place`` の結果を元のファイル名に戻す。

    Args:
        pairs: ``(現在のパス, 元のパス)`` のリスト（``perform_rename_in_place`` の戻り値）。

    Raises:
        OSError: ファイル欠損・戻し先名衝突時。
    """
    if not pairs:
        return

    for cur, orig in pairs:
        if not cur.is_file():
            msg = f"ファイルが見つかりません: {cur}"
            raise OSError(msg)
        if orig.exists():
            msg = f"戻す先に既にファイルがあります: {orig.name}"
            raise OSError(msg)

    for cur, orig in pairs:
        cur.rename(orig)


def pairs_to_serializable(pairs: list[tuple[Path, Path]]) -> list[tuple[str, str]]:
    """シグナル送信用にパスを文字列化する。"""
    return [(str(a), str(b)) for a, b in pairs]


def pairs_from_serializable(raw: object) -> list[tuple[Path, Path]]:
    """シグナル受信後にパスへ戻す。"""
    if not isinstance(raw, list):
        return []
    out: list[tuple[Path, Path]] = []
    for item in raw:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            a, b = item
            if isinstance(a, str) and isinstance(b, str):
                out.append((Path(a), Path(b)))
    return out
