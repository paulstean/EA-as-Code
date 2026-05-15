#!/usr/bin/env python3
"""Validate skill files in the skills/ directory for metadata correctness."""

import os
import re
import sys
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILLS_DIR = os.path.join(ROOT, "skills")

PASS = "PASS"
FAIL = "FAIL"

results = {}


def section(name):
    print(f"\n── {name} ─────────────────────────────────────────────")


def end_section(name, errors, tests):
    if errors:
        results[name] = (FAIL, len(errors), tests)
    else:
        results[name] = (PASS, 0, tests)


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(content, path):
    m = FRONTMATTER_RE.match(content)
    if not m:
        print(f"  ERROR: {path}: missing or invalid YAML frontmatter (must start and end with '---')")
        return None
    try:
        return yaml.safe_load(m.group(1))
    except yaml.YAMLError as ex:
        print(f"  ERROR: {path}: YAML parse error — {ex}")
        return None


# ── 1. Skill Metadata ────────────────────────────────────────────
section("Skill Metadata")

meta_errors = []
meta_count = 0

if not os.path.isdir(SKILLS_DIR):
    print(f"  ERROR: skills/ directory not found at {SKILLS_DIR}")
    sys.exit(1)

skill_files = sorted(f for f in os.listdir(SKILLS_DIR) if f.endswith(".md"))

if not skill_files:
    print("  WARNING: no .md files found in skills/")

for fname in skill_files:
    fpath = os.path.join(SKILLS_DIR, fname)
    with open(fpath) as f:
        content = f.read()

    meta_count += 1
    fm = parse_frontmatter(content, fname)
    if fm is None:
        meta_errors.append(fname)
        continue

    if not isinstance(fm, dict):
        print(f"  ERROR: {fname}: frontmatter must be a mapping, got {type(fm).__name__}")
        meta_errors.append(fname)
        continue

    name = fm.get("name")
    if not name:
        print(f"  ERROR: {fname}: missing required frontmatter field 'name'")
        meta_errors.append(fname)
    elif not isinstance(name, str):
        print(f"  ERROR: {fname}: frontmatter 'name' must be a string, got {type(name).__name__}")
        meta_errors.append(fname)

    description = fm.get("description")
    if not description:
        print(f"  ERROR: {fname}: missing required frontmatter field 'description'")
        meta_errors.append(fname)
    elif not isinstance(description, str):
        print(f"  ERROR: {fname}: frontmatter 'description' must be a string, got {type(description).__name__}")
        meta_errors.append(fname)

    # Name should match filename slug (name == basename without extension)
    expected_name = fname.replace(".md", "")
    if name and name != expected_name:
        print(f"  WARNING: {fname}: frontmatter name '{name}' differs from filename '{expected_name}' (should match)")

end_section("Skill Metadata", meta_errors, meta_count)

# ── Final Summary ───────────────────────────────────────────────
print()
print("=" * 70)
print(f"  {'SUITE':<30} {'RESULT':<8} {'TESTS':<8} ERRORS")
print(f"  {'─'*30} {'─'*8} {'─'*8} ─────")

total_fail = 0
total_tests = 0
total_errors = 0
for name in ["Skill Metadata"]:
    status, err_count, test_count = results.get(name, (PASS, 0, 0))
    total_tests += test_count
    total_errors += err_count
    if status == FAIL:
        total_fail += 1
    print(f"  {name:<30} {status:<8} {test_count:<8} {err_count}")

print()
print(f"  Total: {total_tests} tests, {total_errors} errors")
if total_fail:
    print(f"  ❌  {total_fail} of {len(results)} suites FAILED")
    sys.exit(1)
else:
    print(f"  ✅  ALL {len(results)} suites PASSED")
