# paper-ja-translate

arXiv 論文の LaTeX ソースを使い，レイアウトと図をそのままにして本文だけを日本語に置き換えた PDF を作るための道具．

PDF を直接編集するのではなく，投稿時の LaTeX ソースの英文を訳してコンパイルし直す．
そのため，2段組・数式・図の位置・引用番号は原文と同じになる．

**このリポジトリに論文の本文や訳文は含まない．** 取得したソースと訳文は `work/` に置かれ，`.gitignore` で除外される．

## ライセンスについて

全文訳は原論文の翻案（改変）にあたる．そのため，`fetch_arxiv.py` は最初に arXiv のライセンス表記を確認し，
翻訳を許すライセンスの場合だけソースを取得する．

| ライセンス | 扱い |
|---|---|
| CC BY，CC BY-SA，CC0 | 取得する |
| CC BY-NC，CC BY-NC-SA | 取得する．訳文を営利目的で使わない |
| CC BY-ND，CC BY-NC-ND | 中止する（改変禁止） |
| arXiv 標準ライセンス（non-exclusive distribution） | 中止する（翻訳の許諾がない） |

CC ライセンスでは出典の表示が必要なので，訳文の著者欄の下に `\JaTranslationNote`（原論文の書誌情報，ライセンス，非公式訳である旨）を置く．
中止された論文は，全文訳ではなく要約などで対応する．

## 必要なもの

- TeX Live（`latexmk`，`pdflatex`，`bxcjkjatype`．必要に応じて `luatexja`，`xeCJK`）
- 日本語フォント（IPAex または Noto CJK JP）
- Python 3.12 以降，Pillow
- `pdftoppm`，`pdfinfo`（poppler-utils）

## 使い方

```bash
# 1. ライセンスを確認してソースを取得する（work/<id>/src/，meta.json）
python scripts/fetch_arxiv.py 2605.15583

# 2. 日本語訳の作業用コピーを作る（work/<id>/ja/）
python scripts/prepare_ja.py work/2605.15583

# 3. ja/ の英文を日本語に置き換える（TRANSLATION_GUIDE.md に従う）

# 4. 訳し漏れと，数式・引用などの欠落を検査する
python scripts/check_ja.py work/2605.15583

# 5. 原文と訳文をコンパイルし，ページを並べた比較画像を作る
bash scripts/build.sh work/2605.15583
#   -> work/2605.15583/2605.15583_ja.pdf，2605.15583_en.pdf，compare/page-XX.png
```

```
arXiv 2605.15583 を日本語訳して
```

## 各スクリプトが行うこと

| スクリプト | 内容 |
|---|---|
| `scripts/fetch_arxiv.py` | arXiv の abs ページでライセンスを判定し，許される場合だけ e-print（LaTeX ソース）を取得・展開する．書誌情報を `meta.json` に保存する |
| `scripts/prepare_ja.py` | `src/` を `ja/` にコピーする．主ファイルの `\documentclass` の直後に `\input{ja_engine}`（日本語組版のパッケージ．論文が既に読み込んでいれば入れない）を，`\begin{document}` の直前に `\input{ja_preamble}`（図・表・概要・参考文献の見出し名，cleveref の日本語書式，出典表記マクロ）を入れる．class / style ファイルに直書きされた `Fig.`，`TABLE`，`References`，`Abstract` を置き換え，置き換えきれない箇所を報告する |
| `scripts/check_ja.py` | 訳文ファイルの欠落と，英単語が5語以上続く行を報告する．`\cite`，`\ref`，`\label`，`\includegraphics`，数式の個数をファイルごとに原文と比べる．`\JaTranslationNote` の有無を確認する |
| `scripts/build.sh` | 原文と訳文を `latexmk` でコンパイルし，`compare_pages.py` で左右に並べた比較画像を作る |

## 限界

- 図の中の文字は訳せない（図は PDF や画像として埋め込まれているため）．
- 参考文献リストは原文のまま．
- LaTeX ソースが公開されていない論文には使えない．
- class ファイルの作りによっては見出しの英語が残る．その場合は `prepare_ja.py` の `[check]` 出力の行を手で直す．
- 訳文の品質は訳した人（またはモデル）による．非公式訳であり，正確さは原文で確認すること．

## 開発時の検証

```bash
python -m unittest discover -s tests -v
```

ネットワークや TeX 環境を使わず，文字のエスケープ，UTF-8 の読み書き，エンジンの選択，
訳文ファイルの欠落検出を確認する．`prepare_ja.py --force` で入力が不正な場合は，既存の訳文を残す．

## ライセンス

このリポジトリのコードと文書は MIT License．訳した論文のライセンスは各論文に従う．
