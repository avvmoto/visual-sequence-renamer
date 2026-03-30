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

## ライセンス

[MIT License](LICENSE)

再利用・改変・商用利用を含め、ソフトウェアおよびドキュメントを自由に利用できます。利用は自己責任で、作者は保証しません。

## English summary

**renamer** is a cross-platform (macOS / Windows) desktop app built with PySide6. Drop files, reorder them, then batch-rename to `001_originalname.ext` into a timestamped or custom output folder. Licensed under the **MIT License** — use freely for any purpose.
