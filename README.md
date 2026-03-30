# ならべて連番リネーマー（Visual Sequence Renamer）

**無料のフリーソフト**です。ソースコードは公開された **オープンソース（MIT License）** であり、利用・改変・再配布はライセンスの範囲内で自由です。

ドラッグ＆ドロップでファイルを並べ替え、指定した順で `001_元の名前.ext` 形式に連番リネームするデスクトップアプリです。macOS / Windows 向け（PySide6 / Qt6）。

**名前について:** 画面上で並べた順に連番でリネームする体験を表す **ならべて連番リネーマー**、英語名 **Visual Sequence Renamer** です。Python パッケージ名およびコマンドは短い **`renamer`** のままです（`pip install renamer` / `uv run renamer` など）。Windows 向け PyInstaller 成果物は **`VisualSequenceRenamer.exe`**（単一ファイル）。GitHub Release / CI Artifact では **`VisualSequenceRenamer.zip`**（中身は exe のみ）を配布します。

## 機能

- ファイルのドラッグ＆ドロップでリストに追加
- 画像はサムネイル表示、それ以外は形式に応じたアイコン
- リスト内をドラッグして並べ替え（連番の順序に直結）
- 出力はデフォルトで `renamed_YYYYMMDD_HHMM` フォルダ、または任意の出力先を指定可能
- サムネイル生成・リネームはバックグラウンド処理（UI をブロックしにくい）

詳細な仕様は [spec.md](spec.md) を参照してください。

## 操作デモ（動画）

追加・並べ替え・リネームまでの一連の操作を [docs/public/images/trust/renamer.webm](docs/public/images/trust/renamer.webm) で確認できます（ランディングページでは同内容の MP4 をループ再生しています）。

<video src="docs/public/images/trust/renamer.webm" controls loop muted playsinline width="100%"></video>

## 必要環境

- Python 3.10 以上
- [uv](https://docs.astral.sh/uv/)（推奨）または pip

## セットアップと起動

```bash
# リポジトリをクローンしてプロジェクトルートに移動したうえで
uv sync
uv run renamer
```

開発用に依存だけ入れる場合（Lint / テスト）:

```bash
uv sync --group dev
```

PyInstaller で Windows 用 exe を試す場合は、さらに **`build` グループ**（`pyproject.toml` の `[dependency-groups] build`）を有効にしてください。

```bash
uv sync --group dev --group build
# またはすべてのグループ: uv sync --all-groups
```

## 開発

| 用途 | コマンド |
|------|----------|
| テスト | `uv run pytest` |
| Lint | `uv run ruff check .` |
| 整形 | `uv run ruff format .` |
| 型チェック | `uv run mypy` |

Windows 向けビルドはリポジトリ直下の **`VisualSequenceRenamer.spec`**（`onefile`・未使用 Qt モジュール除外）と [.github/workflows/build.yml](.github/workflows/build.yml) を参照してください。ローカル例: `uv sync --group build` のうえ `uv run pyinstaller --noconfirm VisualSequenceRenamer.spec` → `dist/VisualSequenceRenamer.exe`。

## アイコンの差し替え

アプリ表示用は `src/app/resources/app_icon.png`、Windows の EXE アイコンは `src/app/resources/app_icon.ico` です。ソースは**正方形**（例: 1024×1024）を推奨します。横長・縦長のまま `resize` だけで ICO を作ると、短辺方向に引き伸ばされて**縮尺比が崩れる**ので注意してください。

角の外側が白などで塗りつぶされていると、macOS / Windows のタイトルバーやタスクバーで**四角い板**のように見えます。**PNG を差し替えたあと**は、次のコマンドで「正方形化 → 角丸マスクで外周を透過 → PNG 上書き → ICO 生成」まで一気に行えます（角丸の半径は辺長の約 22.37%、一般的なアプリアイコンに近い比率です）。PyInstaller の `--icon` が参照する ICO も更新されます。

```bash
uv run python -c "
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

RADIUS_RATIO = 0.2237
path = Path('src/app/resources/app_icon.png')
img = Image.open(path).convert('RGBA')
w, h = img.size
side = min(w, h)
left = (w - side) // 2
top = (h - side) // 2
square = img.crop((left, top, left + side, top + side))
square = square.resize((1024, 1024), Image.Resampling.LANCZOS)
sw, sh = square.size
radius = max(1, int(min(sw, sh) * RADIUS_RATIO))
mask = Image.new('L', (sw, sh), 0)
draw = ImageDraw.Draw(mask)
draw.rounded_rectangle((0, 0, sw, sh), radius=radius, fill=255)
alpha = square.split()[3]
square.putalpha(ImageChops.multiply(alpha, mask))
square.save(path, format='PNG')
sizes = [256, 128, 64, 48, 32, 24, 16]
icos = [square.resize((s, s), Image.Resampling.LANCZOS) for s in sizes]
icos[0].save('src/app/resources/app_icon.ico', format='ICO', append_images=icos[1:])
"
```

## ライセンス

[MIT License](LICENSE)

再利用・改変・商用利用を含め、ソフトウェアおよびドキュメントを自由に利用できます。利用は自己責任で、作者は保証しません。不具合報告や改善のプルリクエストは歓迎します（保証はありません）。

## English summary

**Visual Sequence Renamer** (Japanese: **ならべて連番リネーマー**) is a **free** cross-platform (macOS / Windows) desktop app built with PySide6. Drop files, reorder them, then batch-rename to `001_originalname.ext` in the same folder. **Open source** under the **MIT License** — use freely for any purpose. The installable Python package / CLI command remains **`renamer`** for brevity. Windows releases ship **`VisualSequenceRenamer.zip`** containing a single **`VisualSequenceRenamer.exe`**.
