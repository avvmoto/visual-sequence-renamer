---
hero:
  titleJa: ならべて連番リネーム
  titleEn: Visual Sequence
  subtitle: 並べた順のまま、同一フォルダで一括リネーム。
  downloadLabel: Windows 版をダウンロード（ZIP・最新リリース）
  downloadMacLabel: macOS 版をダウンロード（.app ZIP・最新リリース）
  badge: 無料 · オープンソース（MIT）

features:
  - id: image
    title: 画像に強いリスト
    description: 画像はアスペクト比を維持したサムネイルで表示。非画像は OS / Qt のファイルアイコン。長いファイル名は省略表示し、ツールチップでフルネームを確認できます。
  - id: dnd
    title: ドラッグ＆ドロップ
    description: Finder / エクスプローラーからドロップして追加。リスト内をドラッグして並べ替え、ソート（名前・日時など）とも組み合わせ可能です。
  - id: sequence
    title: 連番の自動付与
    description: 画面上の並び順どおりに `001_元の名前.ext` 形式でリネーム。桁数は件数に応じて自動調整。オプションで既存の連番プレフィックスを整理してから付け直せます。

steps:
  - title: ファイルを並べる
    caption: ドラッグ＆ドロップで追加し、ドラッグやソートで希望の順に並べます。
  - title: 順序を確かめる
    caption: 表示されている上から下（行順）が、そのまま連番になる順序です。
  - title: リネーム実行
    caption: 「リネーム実行」で同一フォルダ内を一括変更。直近の操作は元に戻しにも対応します。

footer:
  copyright: © Visual Sequence Renamer
  note: 開発時は `uv run renamer` でも起動可能。配布版は Windows は ZIP 内の SmartRenamer.exe、macOS は ZIP を展開した SmartRenamer.app（未署名のため初回は「開く」が必要な場合あり）。
---

## このアプリについて

**ならべて連番リネーマー**（英語名 **Visual Sequence Renamer**）は、同一フォルダ内のファイルだけを対象に、**表示順どおり**連番付きファイル名へリネームするデスクトップアプリです。処理はバックグラウンド（`QThread`）で行い、UI をブロックしにくい構成です。

ソースコードは GitHub で公開しています。不具合報告や改善のプルリクエストも歓迎します。
