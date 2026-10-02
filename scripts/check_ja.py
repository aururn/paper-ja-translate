#!/usr/bin/env python3
"""訳文 ja/ を原文 src/ と比べて検査する．

使い方:
    python scripts/check_ja.py work/<id>

検査すること:
    1. 英文のまま残っている行（英単語が5語以上続く行）
    2. 数式・引用・参照・ラベル・図の読み込みの個数が原文と一致するか（消し忘れ・消しすぎの検出）
    3. 出典表記 \\JaTranslationNote が本文で使われているか
問題があれば終了コード1を返す．
"""
import argparse
import re
import sys
from pathlib import Path

KEEP_ARG_CMDS = r"(?:cite\w*|ref|eqref|cref|Cref|autoref|label|url|href|includegraphics|input|include|" \
    r"bibliography\w*|begin|end|usepackage|documentclass|newcommand|renewcommand|def|hypersetup|" \
    r"mathcal|mathrm|mathbf|mathbb|operatorname|text|textsc|texttt|color|textcolor|definecolor|" \
    r"vspace|hspace|setlength|resizebox|multicolumn|multirow|cline|cmidrule|arraystretch)"
COUNTED = {
    "\\cite": re.compile(r"\\cite\w*\{([^}]*)\}"),
    "\\ref/\\eqref/\\cref": re.compile(r"\\(?:ref|eqref|cref|Cref|autoref)\{([^}]*)\}"),
    "\\label": re.compile(r"\\label\{([^}]*)\}"),
    "\\includegraphics": re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}"),
    "数式環境": re.compile(r"\\begin\{(equation|align|gather|multline|eqnarray)\*?\}"),
    "インライン数式": re.compile(r"(?<!\\)\$[^$]+(?<!\\)\$"),
}
MATH_ENVS = re.compile(r"\\begin\{(equation|align|gather|multline|eqnarray|lstlisting|verbatim|algorithmic)\*?\}"
                       r".*?\\end\{\1\*?\}", re.S)
ENGLISH_RUN = re.compile(r"[A-Za-z][A-Za-z'\-]{1,}(?:[ ,;:()]+[A-Za-z][A-Za-z'\-]*){4,}")


PROSE_MARKERS = re.compile(r"\\(section|subsection|paragraph|caption|item|begin\{(abstract|figure|table)|maketitle)\b")


def has_prose(t):
    """マクロ定義だけのファイル（preamble 用）を除くため，本文らしい要素があるかを見る．"""
    return bool(PROSE_MARKERS.search(t))


def strip_comments(t):
    return re.sub(r"(?<!\\)%.*", "", t)


def prose_only(t):
    t = strip_comments(t)
    t = MATH_ENVS.sub(lambda m: "\n" * m.group(0).count("\n"), t)
    t = re.sub(r"\\\[.*?\\\]", lambda m: "\n" * m.group(0).count("\n"), t, flags=re.S)
    t = re.sub(r"(?<!\\)\$[^$]*(?<!\\)\$", "", t)
    t = re.sub(r"\\" + KEEP_ARG_CMDS + r"\*?(?:\[[^\]]*\])?\{[^{}]*\}", "", t)
    return t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir")
    ap.add_argument("--allow-english", type=int, default=0, help="許容する英文行の数（既定 0）")
    args = ap.parse_args()
    work = Path(args.workdir)
    src, ja = work / "src", work / "ja"
    problems = 0

    english = []
    note_used = False
    for p in sorted(ja.rglob("*.tex")):
        if p.name == "ja_preamble.tex":
            continue
        rel = p.relative_to(ja)
        t = p.read_text(errors="replace")
        if re.search(r"^[^%\n]*\\JaTranslationNote", t, re.M):
            note_used = True
        body = prose_only(t)
        if not has_prose(body):
            body = ""
        doc = re.search(r"^[^%\n]*\\begin\{document\}", body, re.M)
        if doc:  # 主ファイルの preamble 部分は見ない（行番号は保つ）
            body = "\n" * body[:doc.start()].count("\n") + body[doc.start():]
        for i, line in enumerate(body.splitlines(), 1):
            line = re.sub(r"（[^（）]*）", "", line)  # 用語に添えた英語は数えない
            if ENGLISH_RUN.search(line):
                english.append(f"  {rel}:{i}: {line.strip()[:110]}")

        sp = src / rel
        if sp.exists():
            s_text, j_text = strip_comments(sp.read_text(errors="replace")), strip_comments(t)
            for name, pat in COUNTED.items():
                a, b = len(pat.findall(s_text)), len(pat.findall(j_text))
                if a != b:
                    print(f"[count] {rel}: {name} が原文 {a} 個，訳文 {b} 個")
                    problems += 1

    if english:
        print(f"[english] 英文が残っている可能性のある行: {len(english)}")
        print("\n".join(english[:50]))
        if len(english) > args.allow_english:
            problems += 1
    if not note_used:
        print("[note] \\JaTranslationNote が本文で使われていない（出典表記が必要）．著者欄か脚注に置くこと．")
        problems += 1

    print("[ok] 問題なし" if problems == 0 else f"[ng] 確認が必要な項目: {problems}")
    sys.exit(0 if problems == 0 else 1)


if __name__ == "__main__":
    main()
