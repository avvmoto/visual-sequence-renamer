# renamer (Smart File Renamer)

ドラッグ＆ドロップでファイルを並べ替え、指定した順で `001_元の名前.ext` 形式に連番リネームするデスクトップアプリです。macOS / Windows 向け（PySide6）。

## 機能

- ファイルのドラッグ＆ドロップでリストに追加
- 画像はサムネイル表示、それ以外は形式に応じたアイコン
- リスト内をドラッグして並べ替え（連番の順序に直結）
- 出力はデフォルトで `renamed_YYYYMMDD_HHMM` フォルダ、または任意の出力先を指定可能
- サムネイル生成・リネームはバックグラウンド処理（UI をブロックしにくい）

詳細な仕様は [spec.md](spec.md) を参照してください。

## 必要環境

- Python 3.10 以上
- [uv](https://docs.astral.sh/uv/)（推奨）または pip

## セットアップと起動

```bash
# リポジトリをクローンしてプロジェクトルートに移動したうえで
uv sync
uv run renamer
```

開発用に依存だけ入れる場合:

```bash
uv sync --all-groups
```

## 開発

| 用途 | コマンド |
|------|----------|
| テスト | `uv run pytest` |
| Lint | `uv run ruff check .` |
| 整形 | `uv run ruff format .` |
| 型チェック | `uv run mypy` |

Windows 向け単体 EXE のビルド例（PyInstaller）は [.github/workflows/build.yml](.github/workflows/build.yml) を参照してください。

## アイコンの差し替え

アプリ表示用は `src/app/resources/app_icon.png`、Windows の EXE アイコンは `src/app/resources/app_icon.ico` です。ソースは**正方形**（例: 1024×1024）を推奨します。横長・縦長のまま `resize` だけで ICO を作ると、短辺方向に引き伸ばされて**縮尺比が崩れる**ので注意してください。

**PNG を差し替えたあと**は、次のコマンドで「中央を正方形にクロップ → 1024×1024 にそろえる → PNG を上書き → ICO を生成」まで一気に行えます（PyInstaller の `--icon` が参照する ICO も更新されます）。

```bash
uv run python -c "
from pathlib import Path
from PIL import Image

path = Path('src/app/resources/app_icon.png')
img = Image.open(path).convert('RGBA')
w, h = img.size
side = min(w, h)
left = (w - side) // 2
top = (h - side) // 2
square = img.crop((left, top, left + side, top + side))
square = square.resize((1024, 1024), Image.Resampling.LANCZOS)
square.save(path, format='PNG')
sizes = [256, 128, 64, 48, 32, 24, 16]
icos = [square.resize((s, s), Image.Resampling.LANCZOS) for s in sizes]
icos[0].save('src/app/resources/app_icon.ico', format='ICO', append_images=icos[1:])
"
```

## ライセンス

[MIT License](LICENSE)

再利用・改変・商用利用を含め、ソフトウェアおよびドキュメントを自由に利用できます。利用は自己責任で、作者は保証しません。

## English summary

**renamer** is a cross-platform (macOS / Windows) desktop app built with PySide6. Drop files, reorder them, then batch-rename to `001_originalname.ext` into a timestamped or custom output folder. Licensed under the **MIT License** — use freely for any purpose.
