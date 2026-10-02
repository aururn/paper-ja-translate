# CLAUDE.md

このリポジトリは，arXiv 論文の LaTeX ソースを日本語に訳し，原文と同じレイアウトの PDF を作る道具である．

「arXiv XXXX.XXXXX を日本語訳して」と頼まれたら，次の順に進める．

1. `python scripts/fetch_arxiv.py <id>` を実行する．
   ライセンスの判定で中止された場合（終了コード2）は，全文訳を作らない．
   その旨とライセンス名を伝え，代わりに要約などで対応できることを伝える．
2. `python scripts/prepare_ja.py work/<id>` を実行し，出力の `[check]` 行を確認する．
3. 原文の `src/` を最初から最後まで読み，`TRANSLATION_GUIDE.md` の規則と `glossary.md` の訳語に従って `ja/` の英文を日本語に置き換える．
   ファイル全体を書き直す場合も，数式・コマンド・ラベル・引用は原文から変えない．
4. 著者欄の下などに `\JaTranslationNote` を置く．
5. `python scripts/check_ja.py work/<id>` を実行し，指摘がなくなるまで直す．
   出典表記の段落など，意図して残す英文は `--allow-english N` で許容してよい．
6. `bash scripts/build.sh work/<id>` を実行する．`compare/` の比較画像を見て，崩れ，文字化け，英語の見出しの残りがないかを確認する．
7. 次を報告する．
   - 出力 PDF のパスとページ数（原文と比べて）
   - 原文のまま残したもの（図中の文字，参考文献など）
   - 原文で見つけた誤りや食い違い（訳では直していないこと）
   - 新しく決めた訳語．`glossary.md` にも追記する

- `work/` の中身（論文のソース，訳文，PDF）は commit しない．
- 文書の句読点は「．」「，」を使う．
