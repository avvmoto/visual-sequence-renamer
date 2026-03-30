---
hero:
  titleJa: ならべて連番リネーマー
  titleEn: Visual Sequence Renamer
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

how:
  title: 使い方
  lead: 次の動画は、追加・並べ替え・リネームまでの操作を一通り行った例です。ループ再生されます。

steps:
  - title: ファイルを並べる
    caption: ドラッグ＆ドロップで追加し、ドラッグやソートで希望の順に並べます。
  - title: 順序を確かめる
    caption: 表示されている上から下（行順）が、そのまま連番になる順序です。
  - title: リネーム実行
    caption: 「リネーム実行」で同一フォルダ内を一括変更。直近の操作は元に戻しにも対応します。

trust:
  title: セキュリティと信頼について
  intro: "本ソフトは個人開発のフリーソフトであり、高額なデジタル署名を行っていないため、OS のセキュリティ機能により警告が表示されます。しかし、本ソフトは完全なオープンソースであり、ビルド工程（GitHub Actions）もすべて公開されています。ソースコードを検証し、安全であることを確認してご利用いただけます。"
  windowsTitle: Windows での起動（「PC を保護しました」などと表示された場合）
  windowsSteps:
    - "警告画面で **「詳細情報」** をクリックします。"
    - "表示された **「実行」** ボタンをクリックします。"
  windowsImage:
    src: images/trust/win_warn.png
    alt: Windows に表示される保護メッセージの例（SmartScreen など）
  macTitle: macOS での起動（警告が出た場合）
  macSteps:
    - "警告画面を **「完了」** で閉じます。"
    - "**「システム設定」** ＞ **「プライバシーとセキュリティ」** を開きます。"
    - '下部の「"Visual Sequence Renamer" はブロックされました」の横にある **「このまま開く」** をクリックします。'
  macImages:
    - src: images/trust/mac_warn1.png
      alt: macOS に表示されるブロック通知の例（1）
    - src: images/trust/mac_warn2.png
      alt: プライバシーとセキュリティで「このまま開く」を選ぶ例（2）
  sourceCta: ソースコードを確認する

footer:
  copyright: © Visual Sequence Renamer
  note: 開発時は `uv run renamer` でも起動できます。配布版は Windows は ZIP 内の SmartRenamer.exe、macOS は ZIP を展開した SmartRenamer.app。初回起動時は OS の警告が出ることがあります（上記の手順を参照）。
---

## このアプリについて

**ならべて連番リネーマー**（英語名 **Visual Sequence Renamer**）は、同一フォルダ内のファイルだけを対象に、**表示順どおり**連番付きファイル名へリネームするデスクトップアプリです。

ソースコードは GitHub で公開しています。不具合報告や改善のプルリクエストも歓迎します。
