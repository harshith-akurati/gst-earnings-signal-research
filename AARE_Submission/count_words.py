#!/usr/bin/env python3
"""Reproducible abstract word count. Excludes the title. Counts whitespace-
separated tokens in ABSTRACT.txt, which contains the abstract body only."""
import re, sys, hashlib
from pathlib import Path
p = Path(__file__).resolve().parent / "ABSTRACT.txt"
text = p.read_text(encoding="utf-8").strip()
words = text.split()
print(f"file      : {p.name}")
print(f"sha256    : {hashlib.sha256(p.read_bytes()).hexdigest()}")
print(f"characters: {len(text)}")
print(f"paragraphs: {len([b for b in text.split(chr(10)+chr(10)) if b.strip()])}")
print(f"WORD COUNT: {len(words)}")
print(f"limit 250 : {'PASS' if len(words) <= 250 else 'FAIL'}")
print(f"em dashes : {text.count(chr(8212))} (must be 0)")
print(f"en dashes : {text.count(chr(8211))}")
bad = [w for w in ("TBD","TODO","XXX","PLACEHOLDER","[","]","<",">") if w in text]
print(f"placeholders: {bad if bad else 'none'}")
sys.exit(0 if len(words) <= 250 and text.count(chr(8212)) == 0 and not bad else 1)
