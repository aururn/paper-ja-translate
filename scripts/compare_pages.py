#!/usr/bin/env python3
"""原文 PDF と訳文 PDF を1ページずつ横に並べた画像を作る．

使い方:
    python scripts/compare_pages.py en.pdf ja.pdf out_dir [--dpi 60]
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


def render(pdf, outdir, prefix, dpi):
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", str(pdf), str(outdir / prefix)], check=True)
    return sorted(outdir.glob(f"{prefix}-*.png"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("en_pdf")
    ap.add_argument("ja_pdf")
    ap.add_argument("out_dir")
    ap.add_argument("--dpi", type=int, default=60)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("page-*.png"):
        old.unlink()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        en, ja = render(args.en_pdf, tmp, "en", args.dpi), render(args.ja_pdf, tmp, "ja", args.dpi)
        if len(en) != len(ja):
            print(f"[warn] ページ数が違う：原文 {len(en)}，訳文 {len(ja)}")
        for i in range(max(len(en), len(ja))):
            ims = [Image.open(p) for p in (en[i:i + 1] + ja[i:i + 1])]
            if len(ims) == 1:
                ims = [ims[0], Image.new("RGB", ims[0].size, "white")] if i < len(en) else \
                    [Image.new("RGB", ims[0].size, "white"), ims[0]]
            w, h = sum(im.width for im in ims) + 10, max(im.height for im in ims)
            canvas = Image.new("RGB", (w, h), (128, 128, 128))
            canvas.paste(ims[0], (0, 0))
            canvas.paste(ims[1], (ims[0].width + 10, 0))
            canvas.save(out / f"page-{i + 1:02d}.png")
    print(f"[ok] 比較画像を {out} に保存した（左：原文，右：訳文）．")


if __name__ == "__main__":
    main()
