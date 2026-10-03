import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_ja import detect_engine, prepare_main_text, tex_escape, translation_preamble

ROOT = Path(__file__).resolve().parents[1]
MAIN = "\\documentclass{article}\n\\begin{document}\n\\section{概要}\n日本語本文．\n\\JaTranslationNote\n\\end{document}\n"


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.src = self.work / "src"
        self.ja = self.work / "ja"
        self.src.mkdir()
        (self.src / "main.tex").write_text(MAIN, encoding="utf-8")
        self.meta = {
            "authors": ["著者🍣", "Second"],
            "title": "論文🍣",
            "arxiv_id": "2605.15583",
            "license": "CC BY 4.0",
        }
        (self.work / "meta.json").write_text(
            json.dumps(self.meta, ensure_ascii=False), encoding="utf-8"
        )

    def run_script(self, name, *args):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "0"}
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / name), str(self.work), *args],
            capture_output=True,
            encoding="utf-8",
            env=env,
            check=False,
        )

    def test_escape_does_not_reescape_generated_commands(self):
        self.assertEqual(
            tex_escape("\\{}&%#_$~^"),
            r"\textbackslash{}\{\}\&\%\#\_\$\textasciitilde{}\textasciicircum{}",
        )
        self.assertEqual(tex_escape("日本語🍣"), "日本語🍣")

    def test_metadata_values_do_not_replace_other_template_fields(self):
        self.meta["title"] = "%(license)s & title"
        result = translation_preamble(self.meta)
        self.assertIn(r"\%(license)s \& title", result)
        self.assertIn("著者🍣 et al.", result)
        self.assertIn("CC BY 4.0", result)

    def test_engine_matches_xecjk_and_package_lists(self):
        for packages, engine in (
            ("xeCJK", "xelatex"),
            ("fontspec,xeCJK", "xelatex"),
            ("fontspec", "lualatex"),
            ("amsmath,luatexja", "lualatex"),
        ):
            with self.subTest(packages=packages):
                self.assertEqual(detect_engine(self.src, f"\\usepackage{{{packages}}}"), engine)
        self.assertEqual(detect_engine(self.src, "% \\usepackage{xeCJK}"), "pdflatex")

    def test_arxiv_compiler_metadata_has_priority(self):
        (self.src / "00README.json").write_text(
            json.dumps({"process": {"compiler": "xelatex"}}), encoding="utf-8"
        )
        self.assertEqual(detect_engine(self.src, "\\usepackage{fontspec}"), "xelatex")

    def test_preamble_and_engine_are_inserted_in_order(self):
        text, needs_engine = prepare_main_text(MAIN)
        self.assertTrue(needs_engine)
        self.assertIn("\\documentclass{article}\n\\input{ja_engine}\n", text)
        self.assertIn("\\input{ja_preamble}\n\\begin{document}", text)
        text, needs_engine = prepare_main_text(
            MAIN.replace("\\begin{document}", "\\usepackage{xeCJK}\n\\begin{document}")
        )
        self.assertFalse(needs_engine)
        self.assertNotIn("\\input{ja_engine}", text)

    def test_prepare_round_trips_unicode_and_preserves_the_source(self):
        result = self.run_script("prepare_ja.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.src / "main.tex").read_text(encoding="utf-8"), MAIN)
        self.assertIn("日本語本文", (self.ja / "main.tex").read_text(encoding="utf-8"))
        self.assertIn("論文🍣", (self.ja / "ja_preamble.tex").read_text(encoding="utf-8"))
        info = json.loads((self.ja / ".ja_build.json").read_text(encoding="utf-8"))
        self.assertEqual(info, {"main": "main.tex", "engine": "pdflatex"})

    def test_valid_translation_passes_the_checker(self):
        self.assertEqual(self.run_script("prepare_ja.py").returncode, 0)
        result = self.run_script("check_ja.py")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_force_with_invalid_main_preserves_existing_translation(self):
        self.ja.mkdir()
        translated = self.ja / "main.tex"
        translated.write_text("既存の訳文🍣", encoding="utf-8")
        for args in (("--main", "missing.tex"), ("--main", "../outside.tex")):
            with self.subTest(args=args):
                result = self.run_script("prepare_ja.py", "--force", *args)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(translated.read_text(encoding="utf-8"), "既存の訳文🍣")

    def test_force_with_invalid_tex_preserves_existing_translation(self):
        self.ja.mkdir()
        translated = self.ja / "main.tex"
        translated.write_text("既存の訳文", encoding="utf-8")
        (self.src / "main.tex").write_text("\\documentclass{article}\n", encoding="utf-8")
        result = self.run_script("prepare_ja.py", "--force", "--main", "main.tex")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(translated.read_text(encoding="utf-8"), "既存の訳文")

    def test_force_with_invalid_metadata_preserves_existing_translation(self):
        self.ja.mkdir()
        translated = self.ja / "main.tex"
        translated.write_text("既存の訳文", encoding="utf-8")
        del self.meta["license"]
        (self.work / "meta.json").write_text(json.dumps(self.meta), encoding="utf-8")
        self.assertNotEqual(self.run_script("prepare_ja.py", "--force").returncode, 0)
        self.assertEqual(translated.read_text(encoding="utf-8"), "既存の訳文")

    def test_valid_force_replaces_the_translation(self):
        self.ja.mkdir()
        (self.ja / "old.txt").write_text("old", encoding="utf-8")
        result = self.run_script("prepare_ja.py", "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.ja / "old.txt").exists())
        self.assertTrue((self.ja / "main.tex").is_file())

    def test_deleted_translated_file_is_reported(self):
        self.ja.mkdir()
        (self.ja / "main.tex").write_text(MAIN, encoding="utf-8")
        (self.src / "section.tex").write_text("\\section{追加}\n", encoding="utf-8")
        result = self.run_script("check_ja.py")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("[missing] section.tex", result.stdout)

    def test_missing_source_directory_is_rejected(self):
        self.ja.mkdir()
        (self.ja / "main.tex").write_text(MAIN, encoding="utf-8")
        (self.src / "main.tex").unlink()
        self.src.rmdir()
        self.assertEqual(self.run_script("check_ja.py").returncode, 2)


if __name__ == "__main__":
    unittest.main()
