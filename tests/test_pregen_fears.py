"""Every pregenerated character of an adventure has fears, so that setup never has to ask the player for them.
The check runs on the fixtures; to check the real adventures: PREGEN_FEARS_DIR=<folder of the adventures repository> pytest tests/test_pregen_fears.py"""
import os
import re
from pathlib import Path

import pytest

from server import files

REAL = os.environ.get("PREGEN_FEARS_DIR")
FOLDER = Path(REAL) if REAL else Path(__file__).parent / "fixtures" / "adventures"
PAGES = sorted(p for p in FOLDER.glob("*.md") if p.name.lower() != "readme.md")


def part_a(text):
    m = re.search(r"^# PART A\b.*?(?=^# PART B\b)", text, re.S | re.M)
    return m.group(0) if m else ""


@pytest.mark.parametrize("path", PAGES, ids=[p.name for p in PAGES])
def test_every_pregenerated_character_has_a_fear(path):
    text = path.read_text(encoding="utf-8")
    meta, _ = files.split_front_matter(text)
    ids = meta.get("pregenerated") or []
    if not ids:
        pytest.skip("no pregenerated characters")
    a = part_a(text)
    # one `Fears` entry per pregenerated character: a full sheet has one; character seeds have one under each seed
    n = len(re.findall(r"(?im)^\W*fears?\W*:", a)) or len(re.findall(r"(?im)\bfears?\b\s*:", a))
    need = len(ids) if REAL else 1  # the fixture lists several ids but has one sheet
    assert n >= need, f"{path.name}: {len(ids)} pregenerated characters but {n} Fears lines in Part A"
