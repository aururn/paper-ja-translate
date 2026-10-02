#!/usr/bin/env bash
# 原文 src/ と訳文 ja/ をコンパイルし，ページを並べた比較画像を作る．
#
# 使い方:
#   bash scripts/build.sh work/<id>            # 原文と訳文をビルドして比較画像を作る
#   bash scripts/build.sh work/<id> --ja-only  # 訳文だけビルドする
#
# 出力:
#   work/<id>/<id>_en.pdf, work/<id>/<id>_ja.pdf
#   work/<id>/compare/page-XX.png（左が原文，右が訳文）
set -euo pipefail

WORK=$(cd "$1" && pwd)
JA_ONLY=${2:-}
ID=$(basename "$WORK")
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)

MAIN=$(python3 -c "import json;print(json.load(open('$WORK/ja/.ja_build.json'))['main'])")
ENGINE=$(python3 -c "import json;print(json.load(open('$WORK/ja/.ja_build.json'))['engine'])")
case "$ENGINE" in
  pdflatex) LATEXMK_FLAG=-pdf ;;
  lualatex) LATEXMK_FLAG=-lualatex ;;
  xelatex)  LATEXMK_FLAG=-xelatex ;;
  *) echo "unknown engine: $ENGINE" >&2; exit 1 ;;
esac

build() {  # $1: ソースのディレクトリ，$2: 出力 PDF
  local dir=$1 out=$2 stem
  stem=${MAIN%.tex}
  ( cd "$dir/$(dirname "$MAIN")" &&
    latexmk -g "$LATEXMK_FLAG" -interaction=nonstopmode "$(basename "$MAIN")" > latexmk.out 2>&1 ) || true
  local log="$dir/$stem.log" pdf="$dir/$stem.pdf"
  if grep -q "^!" "$log" 2>/dev/null; then
    echo "[error] $dir のコンパイルでエラー:" >&2
    grep -A3 "^!" "$log" | head -20 >&2
  fi
  if [ ! -f "$pdf" ]; then
    echo "[error] PDF が作られなかった: $pdf（ログ: $log）" >&2
    exit 1
  fi
  cp "$pdf" "$out"
  echo "[ok] $out（$(pdfinfo "$out" | awk '/^Pages/{print $2}') ページ）"
}

if [ "$JA_ONLY" != "--ja-only" ]; then
  if [ ! -d "$WORK/en_build" ]; then
    cp -r "$WORK/src" "$WORK/en_build"
  fi
  build "$WORK/en_build" "$WORK/${ID}_en.pdf"
fi
build "$WORK/ja" "$WORK/${ID}_ja.pdf"

if [ -f "$WORK/${ID}_en.pdf" ]; then
  python3 "$SCRIPT_DIR/compare_pages.py" "$WORK/${ID}_en.pdf" "$WORK/${ID}_ja.pdf" "$WORK/compare"
fi
