#!/usr/bin/env python3
"""Validate all EA catalog files against JSON standards, meta files, metamodel, and cardinality."""

import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOGS_DIR = os.path.join(ROOT, "catalogs")
METAMODEL_PATH = os.path.join(ROOT, "metamodel.json")

PASS = "PASS"
FAIL = "FAIL"

results = {}  # section_name -> (status, errors_count, tests_count)


def section(name):
    print(f"\n── {name} ─────────────────────────────────────────────")

def end_section(name, errors, tests):
    if errors:
        results[name] = (FAIL, len(errors), tests)
    else:
        results[name] = (PASS, 0, tests)


def load_json(path, label):
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as ex:
        print(f"  ERROR: {label}: Invalid JSON — {ex}")
    except FileNotFoundError:
        print(f"  ERROR: {label}: File not found")
    return None


# ── Load metamodel ──────────────────────────────────────────────
metamodel = load_json(METAMODEL_PATH, "metamodel.json")
if metamodel is None:
    sys.exit(1)

entity_by_catalog = {et["catalog"]: et for et in metamodel["entityTypes"]}
fields_by_entity = {et["name"]: {f["name"]: f for f in et["fields"]} for et in metamodel["entityTypes"]}

ID_PREFIXES = {
    "BusinessUnits": "bu-",
    "BusinessProcesses": "bp-",
    "BusinessActivities": "ba-",
    "BusinessUserGroups": "bug-",
    "DataDomains": "dd-",
    "DataEntities": "de-",
    "ApplicationComponents": "app-",
    "InformationFlows": "flow-",
    "InfrastructureComponents": "infra-",
    "Permissions": "perm-",
    "TechnologyStandards": "ts-",
}

ENUMS = metamodel.get("enums", {})

CARD_TYPE = {
    "one-to-one": "string",
    "many-to-one": "string",
    "one-to-many": "string",
    "many-to-many": "array",
}


def check_field_type(value, expected, field, eid):
    if expected == "array":
        if not isinstance(value, list):
            print(f"  ERROR: {eid}: Field '{field}' must be an array, got {type(value).__name__}")
            return False
    elif expected == "string":
        if value is not None and not isinstance(value, str):
            print(f"  ERROR: {eid}: Field '{field}' must be a string, got {type(value).__name__}")
            return False
    return True


# ── 1. JSON Syntax Check ────────────────────────────────────────
section("JSON Syntax")

json_errors = []
json_count = 0
for cname in sorted(entity_by_catalog):
    fp = os.path.join(CATALOGS_DIR, cname, f"{cname}.json")
    mp = os.path.join(CATALOGS_DIR, cname, f"{cname}-Meta.json")
    for path, label in [(fp, f"{cname}.json"), (mp, f"{cname}-Meta.json")]:
        if os.path.exists(path):
            json_count += 1
            try:
                json.load(open(path))
            except json.JSONDecodeError as ex:
                print(f"  ERROR: {label}: {ex}")
                json_errors.append(label)

end_section("JSON Syntax", json_errors, json_count)

# ── 2. Meta File Structure ──────────────────────────────────────
section("Meta File Structure")

meta_errors = []
meta_count = 0
for cname in sorted(entity_by_catalog):
    mp = os.path.join(CATALOGS_DIR, cname, f"{cname}-Meta.json")
    meta = load_json(mp, f"{cname}-Meta.json")
    if meta is None:
        meta_errors.append(cname)
        continue
    meta_count += 1
    if "fields" not in meta:
        print(f"  ERROR: {cname}-Meta.json: missing 'fields' key")
        meta_errors.append(cname)
    if "catalogName" not in meta:
        print(f"  ERROR: {cname}-Meta.json: missing 'catalogName' key")
        meta_errors.append(cname)

end_section("Meta File Structure", meta_errors, meta_count)

# ── 3. Metamodel Conformance ────────────────────────────────────
section("Metamodel Conformance")

mm_errors = []
mm_count = 0
for cname in sorted(entity_by_catalog):
    fp = os.path.join(CATALOGS_DIR, cname, f"{cname}.json")
    entries = load_json(fp, f"{cname}.json")
    if entries is None or not isinstance(entries, list):
        if entries is None or not isinstance(entries, list):
            print(f"  ERROR: {cname}.json: top-level must be a JSON array")
            mm_errors.append(cname)
        continue

    entity = entity_by_catalog.get(cname)
    if entity is None:
        print(f"  ERROR: {cname}: not defined in metamodel.json entityTypes")
        mm_errors.append(cname)
        continue

    fdefs = fields_by_entity.get(entity["name"], {})

    for entry in entries:
        if not isinstance(entry, dict):
            print(f"  ERROR: {cname}.json: entry is not an object: {entry}")
            mm_errors.append(cname)
            continue

        mm_count += 1
        eid = entry.get("id", f"<no-id-in-{cname}>")

        for fn, fd in fdefs.items():
            if fd.get("required") and fn not in entry:
                print(f"  ERROR: {eid}: missing required field '{fn}' (metamodel)")
                mm_errors.append(eid)

        for fn in entry:
            if fn not in fdefs:
                print(f"  ERROR: {eid}: unknown field '{fn}'")
                mm_errors.append(eid)

        for fn, val in entry.items():
            if fn in fdefs:
                if not check_field_type(val, fdefs[fn]["type"], fn, eid):
                    mm_errors.append(eid)

end_section("Metamodel Conformance", mm_errors, mm_count)

# ── 4. ID Prefix Convention ────────────────────────────────────
section("ID Prefix Convention")

id_errors = []
id_count = 0
for cname in sorted(entity_by_catalog):
    fp = os.path.join(CATALOGS_DIR, cname, f"{cname}.json")
    entries = load_json(fp, f"{cname}.json")
    if not entries:
        continue

    expected_prefix = ID_PREFIXES.get(cname, "")
    if not expected_prefix:
        continue

    for entry in entries:
        id_count += 1
        eid = entry.get("id", "")
        if not str(eid).startswith(expected_prefix):
            print(f"  ERROR: {eid}: ID does not start with expected prefix '{expected_prefix}'")
            id_errors.append(eid)

end_section("ID Prefix Convention", id_errors, id_count)

# ── 5. Cardinality ──────────────────────────────────────────────
section("Cardinality")

card_errors = []
card_count = 0
for cname in sorted(entity_by_catalog):
    entity = entity_by_catalog.get(cname)
    if entity is None:
        continue

    card_map = {}
    for rel in metamodel.get("relationships", []):
        if rel["source"] == entity["name"] and rel.get("viaField"):
            card_map[rel["viaField"]] = rel["cardinality"]

    if not card_map:
        continue

    fp = os.path.join(CATALOGS_DIR, cname, f"{cname}.json")
    entries = load_json(fp, f"{cname}.json")
    if not entries:
        continue

    for entry in entries:
        eid = entry.get("id", "")
        for fn, card in card_map.items():
            if fn not in entry:
                continue
            card_count += 1
            wanted = CARD_TYPE.get(card)
            if wanted == "array" and not isinstance(entry[fn], list):
                print(f"  ERROR: {eid}: field '{fn}' has cardinality {card} but is not an array")
                card_errors.append(eid)
            elif wanted == "string" and isinstance(entry[fn], list):
                print(f"  ERROR: {eid}: field '{fn}' has cardinality {card} but is an array")
                card_errors.append(eid)

end_section("Cardinality", card_errors, card_count)

# ── 6. Enum Values ──────────────────────────────────────────────
section("Enum Values")

enum_errors = []
enum_count = 0
for cname in sorted(entity_by_catalog):
    entity = entity_by_catalog.get(cname)
    if entity is None:
        continue

    fp = os.path.join(CATALOGS_DIR, cname, f"{cname}.json")
    entries = load_json(fp, f"{cname}.json")
    if not entries:
        continue

    for entry in entries:
        eid = entry.get("id", "")

        if entity["name"] == "TechnologyStandard":
            val = entry.get("status")
            if val is not None:
                enum_count += 1
                edef = ENUMS.get("TechnologyStandardStatus")
                if edef and val not in edef["values"]:
                    print(f"  ERROR: {eid}: status '{val}' invalid — allowed: {edef['values']}")
                    enum_errors.append(eid)

        if entity["name"] == "InfrastructureComponent":
            val = entry.get("type")
            if val is not None:
                enum_count += 1
                edef = ENUMS.get("InfrastructureComponentType")
                if edef and val not in edef["values"]:
                    print(f"  ERROR: {eid}: type '{val}' invalid — allowed: {edef['values']}")
                    enum_errors.append(eid)

        if entity["name"] == "Permission":
            val = entry.get("accessLevel")
            if val is not None:
                enum_count += 1
                edef = ENUMS.get("PermissionAccessLevel")
                if edef and val not in edef["values"]:
                    print(f"  ERROR: {eid}: accessLevel '{val}' invalid — allowed: {edef['values']}")
                    enum_errors.append(eid)

end_section("Enum Values", enum_errors, enum_count)

# ── 7. Cross-References ─────────────────────────────────────────
section("Cross-References")

# Build ID index
all_by_id = {}
for cname in sorted(entity_by_catalog):
    fp = os.path.join(CATALOGS_DIR, cname, f"{cname}.json")
    entries = load_json(fp, f"{cname}.json")
    if entries:
        for ent in entries:
            eid = ent.get("id")
            if eid:
                all_by_id[eid] = (cname, ent)

xref_errors = []
xref_count = 0

def check_ref(val, field, source_id):
    global xref_count
    xref_count += 1
    if val is None or val == "":
        return
    if val not in all_by_id:
        print(f"  ERROR: {source_id}: field '{field}' references '{val}' which does not exist")
        xref_errors.append(f"{source_id}.{field}->{val}")

for cname in sorted(entity_by_catalog):
    entity = entity_by_catalog.get(cname)
    if entity is None:
        continue
    fp = os.path.join(CATALOGS_DIR, cname, f"{cname}.json")
    entries = load_json(fp, f"{cname}.json")
    if not entries:
        continue

    for entry in entries:
        eid = entry.get("id", "")
        for rel in metamodel.get("relationships", []):
            if rel["source"] == entity["name"] and rel.get("viaField"):
                field = rel["viaField"]
                if field in entry:
                    val = entry[field]
                    if isinstance(val, list):
                        for v in val:
                            check_ref(v, field, eid)
                    else:
                        check_ref(val, field, eid)

end_section("Cross-References", xref_errors, xref_count)

# ── Final Summary ───────────────────────────────────────────────
print()
print("=" * 70)
print(f"  {'SUITE':<30} {'RESULT':<8} {'TESTS':<8} ERRORS")
print(f"  {'─'*30} {'─'*8} {'─'*8} ─────")

total_fail = 0
total_tests = 0
total_errors = 0
for name in ["JSON Syntax", "Meta File Structure", "Metamodel Conformance",
             "ID Prefix Convention", "Cardinality", "Enum Values", "Cross-References"]:
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
