#!/usr/bin/env python3
"""arXiv 論文のライセンスを確認し，翻訳が許される場合だけ LaTeX ソースを取得する．

使い方:
    python scripts/fetch_arxiv.py 2605.15583 [--work work]

出力:
    work/<id>/src/        展開した LaTeX ソース
    work/<id>/meta.json   書誌情報とライセンス
"""

import argparse
import datetime
import gzip
import io
import json
import re
import sys
import tarfile
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

USER_AGENT = "paper-ja-translate/0.1 (personal translation tool)"

# 翻訳（改変）を許すライセンス．ND（改変禁止）と arXiv 標準ライセンスは含めない．
ALLOWED_LICENSES = {
    "by": "CC BY",
    "by-sa": "CC BY-SA",
    "by-nc": "CC BY-NC",
    "by-nc-sa": "CC BY-NC-SA",
}


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as res:
        return res.read()


def normalize_id(arxiv_id):
    arxiv_id = arxiv_id.strip()
    arxiv_id = re.sub(r"^https?://arxiv\.org/(abs|pdf)/", "", arxiv_id)
    arxiv_id = re.sub(r"\.pdf$", "", arxiv_id)
    return arxiv_id


def check_license(arxiv_id):
    """arXiv の abs ページからライセンスを読み，(許可するか, 名前, URL) を返す．"""
    html = http_get(f"https://arxiv.org/abs/{arxiv_id}").decode("utf-8", "replace")
    m = re.search(r'href="(https?://(?:creativecommons\.org|arxiv\.org/licenses)/[^"]+)"', html)
    if not m:
        return False, "unknown", None
    url = m.group(1)
    cc = re.search(r"creativecommons\.org/licenses/([a-z-]+)/([0-9.]+)", url)
    if cc:
        kind, ver = cc.group(1), cc.group(2)
        name = f"CC {kind.upper()} {ver}"
        if kind in ALLOWED_LICENSES:
            return True, f"{ALLOWED_LICENSES[kind]} {ver}", url
        return False, name, url
    if "creativecommons.org/publicdomain/zero" in url:
        return True, "CC0 1.0", url
    return False, "arXiv non-exclusive license" if "nonexclusive" in url else url, url


def fetch_metadata(arxiv_id):
    xml = http_get(f"https://export.arxiv.org/api/query?id_list={arxiv_id}")
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = ET.fromstring(xml).find("a:entry", ns)
    if entry is None:
        return {}
    title = " ".join(entry.findtext("a:title", "", ns).split())
    authors = [a.findtext("a:name", "", ns) for a in entry.findall("a:author", ns)]
    abs_url = entry.findtext("a:id", "", ns)
    return {"title": title, "authors": authors, "abs_url": abs_url}


def extract_source(data, dest):
    """e-print を展開する．tar.gz，単一の gzip ファイル，PDF のみ，の順に判定する．"""
    if data[:4] == b"%PDF":
        raise RuntimeError("この論文は LaTeX ソースが公開されていない（PDF のみ）．")
    dest.mkdir(parents=True, exist_ok=False)
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tar:
            tar.extractall(dest, filter="data")
        return
    except tarfile.ReadError:
        pass
    try:
        text = gzip.decompress(data)
    except OSError:
        text = data
    (dest / "main.tex").write_bytes(text)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("arxiv_id", help="arXiv ID または abs/pdf の URL")
    ap.add_argument("--work", default="work", help="作業ディレクトリ（既定: work）")
    args = ap.parse_args()

    arxiv_id = normalize_id(args.arxiv_id)
    allowed, lic_name, lic_url = check_license(arxiv_id)
    print(f"[license] {arxiv_id}: {lic_name}")
    if not allowed:
        print(
            "このライセンスは翻訳（改変）を許していないため，処理を中止する．"
            "全文訳ではなく要約などで対応すること．",
            file=sys.stderr,
        )
        sys.exit(2)

    workdir = Path(args.work) / arxiv_id.replace("/", "_")
    src = workdir / "src"
    if src.exists():
        print(f"{src} は既に存在する．取り直す場合は削除してから実行すること．", file=sys.stderr)
        sys.exit(1)

    meta = fetch_metadata(arxiv_id)
    data = http_get(f"https://arxiv.org/e-print/{arxiv_id}")
    workdir.mkdir(parents=True, exist_ok=True)
    extract_source(data, src)

    meta.update(
        {
            "arxiv_id": arxiv_id,
            "license": lic_name,
            "license_url": lic_url,
            "noncommercial": any(k in (lic_url or "") for k in ("/by-nc/", "/by-nc-sa/")),
            "fetched": datetime.date.today().isoformat(),
        }
    )
    (workdir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[ok] {meta.get('title', '')}")
    print(f"[ok] ソースを {src} に展開した．")
    if meta["noncommercial"]:
        print("[note] 非営利ライセンス．訳文を営利目的で使わないこと．")


if __name__ == "__main__":
    main()
