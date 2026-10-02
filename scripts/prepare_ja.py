#!/usr/bin/env python3
"""取得した LaTeX ソースから，日本語訳の作業用コピー ja/ を作る．

使い方:
    python scripts/prepare_ja.py work/<id> [--engine pdflatex|lualatex|xelatex] [--force]

行うこと:
    1. src/ を ja/ にコピーする
    2. 主ファイルを特定し，\\documentclass の直後に \\input{ja_engine}（日本語組版のパッケージ）を，
       \\begin{document} の直前に \\input{ja_preamble}（図表見出し，出典表記マクロ）を入れる
    3. class/sty に直書きされた英語の見出し（Fig.，TABLE，References 等）を置き換える
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

PREAMBLE_COMMON = r"""
% ---- 図表・見出しの名前 ----
\AtBeginDocument{%
  \providecommand{\figurename}{}\renewcommand{\figurename}{図}%
  \providecommand{\tablename}{}\renewcommand{\tablename}{表}%
  \providecommand{\abstractname}{}\renewcommand{\abstractname}{概要}%
  \providecommand{\refname}{}\renewcommand{\refname}{参考文献}%
  \providecommand{\bibname}{}\renewcommand{\bibname}{参考文献}%
  \providecommand{\appendixname}{}\renewcommand{\appendixname}{付録}%
}
\makeatletter
\@ifpackageloaded{cleveref}{%
  \crefformat{figure}{#2図~#1#3}\Crefformat{figure}{#2図~#1#3}%
  \crefformat{table}{#2表~#1#3}\Crefformat{table}{#2表~#1#3}%
  \crefformat{equation}{#2式~(#1)#3}\Crefformat{equation}{#2式~(#1)#3}%
  \crefformat{section}{#2#1節#3}\Crefformat{section}{#2#1節#3}%
  \crefformat{subsection}{#2#1節#3}\Crefformat{subsection}{#2#1節#3}%
  \crefformat{subsubsection}{#2#1節#3}\Crefformat{subsubsection}{#2#1節#3}%
  \crefformat{appendix}{#2付録~#1#3}\Crefformat{appendix}{#2付録~#1#3}%
  \crefformat{algorithm}{#2アルゴリズム~#1#3}\Crefformat{algorithm}{#2アルゴリズム~#1#3}%
}{}
\makeatother

% ---- 出典表記（CC ライセンスの表示義務）．本文の著者欄や脚注に \JaTranslationNote を置く ----
\newcommand{\JaTranslationNote}{%
  （非公式日本語訳．原論文：%(authors)s, ``%(title)s,'' arXiv:%(arxiv_id)s．%
  原論文は %(license)s で公開されており，本訳はそのライセンスに基づき本文を日本語に翻訳したものである．%
  図中の文字と参考文献は原文のまま．訳の誤りは訳者の責任である．）}
"""

# 日本語組版のパッケージ．\documentclass の直後に入れる（後ろで読み込むと文字化けする論文があった）．
PREAMBLE_ENGINE = {
    "pdflatex": "\\usepackage[whole]{bxcjkjatype}\n",
    "lualatex": "\\usepackage{luatexja}\n",
    "xelatex": "\\usepackage{xeCJK}\n\\setCJKmainfont{Noto Serif CJK JP}\n\\setCJKsansfont{Noto Sans CJK JP}\n",
}
CJK_PACKAGE = re.compile(r"^[^%\n]*\\usepackage(\[[^\]]*\])?\{[^}]*\b(bxcjkjatype|luatexja|xeCJK|CJK|CJKutf8)\b", re.M)

# class/sty に直書きされやすい見出し．(説明, 正規表現, 置換) の順．
CLASS_PATCHES = [
    ("図の番号", re.compile(r"(\\def\\fnum@figure\{)(?:Fig\.|Figure)(~|\\ |\s)"), r"\1図~"),
    ("表の番号", re.compile(r"(\\def\\fnum@table\{)(?:TABLE|Table)(~|\\ |\s)"), r"\1表~"),
    ("参考文献の見出し", re.compile(r"(\\section\*?\{)References(\})"), r"\1参考文献\2"),
    ("参考文献の目次項目", re.compile(r"(\\addcontentsline\{toc\}\{section\}\{)References(\})"), r"\1参考文献\2"),
    ("概要の見出し", re.compile(r"(\\text(?:it|bf)\{)Abstract(\})"), r"\1概要\2"),
    ("概要の見出し", re.compile(r"(\\bf(?:series)?\s*)Abstract\b"), r"\1概要"),
    ("キーワードの見出し", re.compile(r"(\\text(?:it|bf)\{)Index Terms(\})"), r"\1キーワード\2"),
]
SUSPICIOUS = re.compile(r"\{[^{}]*\b(References|Abstract|Figure|Fig\.|TABLE|Index Terms)\b")


def find_main_tex(src):
    readme = src / "00README.json"
    if readme.exists():
        info = json.loads(readme.read_text())
        for s in info.get("sources", []):
            if s.get("usage") == "toplevel":
                return src / s["filename"]
    cands = []
    for p in sorted(src.rglob("*.tex")):
        t = p.read_text(errors="replace")
        if re.search(r"^[^%\n]*\\documentclass", t, re.M) and re.search(r"^[^%\n]*\\begin\{document\}", t, re.M):
            cands.append(p)
    if len(cands) != 1:
        names = ", ".join(str(c.relative_to(src)) for c in cands) or "なし"
        raise RuntimeError(f"主ファイルを1つに決められない（候補: {names}）．--main で指定すること．")
    return cands[0]


def detect_engine(src, main_text):
    readme = src / "00README.json"
    if readme.exists():
        comp = json.loads(readme.read_text()).get("process", {}).get("compiler", "")
        for e in ("lualatex", "xelatex", "pdflatex"):
            if e in comp:
                return e
    if re.search(r"^[^%\n]*\\usepackage(\[[^\]]*\])?\{(fontspec|unicode-math|luatexja|xeCJK)\}", main_text, re.M):
        return "lualatex"
    return "pdflatex"


def tex_escape(s):
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("#", r"\#"),
                 ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("$", r"\$")):
        s = s.replace(a, b)
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir")
    ap.add_argument("--engine", choices=sorted(PREAMBLE_ENGINE))
    ap.add_argument("--main", help="主ファイル（src からの相対パス）")
    ap.add_argument("--force", action="store_true", help="既存の ja/ を消して作り直す")
    args = ap.parse_args()

    work = Path(args.workdir)
    src, ja = work / "src", work / "ja"
    meta = json.loads((work / "meta.json").read_text())
    if ja.exists():
        if not args.force:
            print(f"{ja} は既に存在する（訳文を上書きしないため中止）．作り直す場合は --force．", file=sys.stderr)
            sys.exit(1)
        shutil.rmtree(ja)
    shutil.copytree(src, ja)

    main_src = src / args.main if args.main else find_main_tex(src)
    main_ja = ja / main_src.relative_to(src)
    text = main_ja.read_text(errors="replace")
    engine = args.engine or detect_engine(src, text)

    m = re.search(r"^([^%\n]*?)\\begin\{document\}", text, re.M)
    if not m:
        raise RuntimeError("\\begin{document} が見つからない．")
    pos = m.start() + len(m.group(1))
    text = text[:pos] + "\\input{ja_preamble}\n" + text[pos:]
    if CJK_PACKAGE.search(text):
        print("[engine] 論文が既に日本語（CJK）パッケージを読み込んでいるので追加しない．")
    else:
        m = re.search(r"^[^%\n]*?\\documentclass\s*(\[[^\]]*\])?\s*\{[^}]*\}[^\n]*\n", text, re.M)
        if not m:
            raise RuntimeError("\\documentclass が見つからない．")
        text = text[:m.end()] + "\\input{ja_engine}\n" + text[m.end():]
        (main_ja.parent / "ja_engine.tex").write_text(
            "% prepare_ja.py が生成．日本語組版のパッケージ．\n" + PREAMBLE_ENGINE[engine])
    main_ja.write_text(text)

    authors = meta.get("authors", [])
    author_str = authors[0] + (" et al." if len(authors) > 1 else "") if authors else "(著者不明)"
    preamble = "% prepare_ja.py が生成．必要に応じて編集してよい．\n"
    preamble += PREAMBLE_COMMON.replace("%(authors)s", tex_escape(author_str)) \
        .replace("%(title)s", tex_escape(meta.get("title", ""))) \
        .replace("%(arxiv_id)s", tex_escape(meta["arxiv_id"])) \
        .replace("%(license)s", tex_escape(meta["license"]))
    (main_ja.parent / "ja_preamble.tex").write_text(preamble)

    print(f"[main] {main_ja.relative_to(work)}  [engine] {engine}")
    for p in sorted(list(ja.rglob("*.cls")) + list(ja.rglob("*.sty"))):
        t = p.read_text(errors="replace")
        for desc, pat, rep in CLASS_PATCHES:
            t, n = pat.subn(rep, t)
            if n:
                print(f"[patch] {p.relative_to(work)}: {desc}を置換（{n}箇所）")
        p.write_text(t)
        for i, line in enumerate(t.splitlines(), 1):
            if not line.lstrip().startswith("%") and SUSPICIOUS.search(line):
                print(f"[check] {p.relative_to(work)}:{i}: 英語の見出しが残っている可能性: {line.strip()[:100]}")

    (ja / ".ja_build.json").write_text(json.dumps(
        {"main": str(main_ja.relative_to(ja)), "engine": engine}, indent=2) + "\n")
    print(f"[ok] {ja} を作成した．次は TRANSLATION_GUIDE.md に従って本文を訳す．")


if __name__ == "__main__":
    main()
