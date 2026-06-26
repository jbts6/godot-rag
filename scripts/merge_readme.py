#!/usr/bin/env python3
"""Merge English and Chinese READMEs into a single file for PyPI."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    en = (ROOT / "README.md").read_text(encoding="utf-8")
    zh = (ROOT / "README_zh.md").read_text(encoding="utf-8")

    # Remove cross-language links
    en = en.replace("[中文版](README_zh.md)\n\n", "")
    zh = zh.replace("[English](README.md)\n\n", "")

    # Remove the Chinese title (duplicate of English)
    zh_lines = zh.split("\n")
    if zh_lines and zh_lines[0].startswith("# "):
        zh_lines = zh_lines[1:]
    zh = "\n".join(zh_lines).lstrip("\n")

    merged = en.rstrip("\n") + "\n\n---\n\n" + zh

    out = ROOT / "README_PYPI.md"
    out.write_text(merged, encoding="utf-8")
    print(f"Written: {out}")


if __name__ == "__main__":
    main()
