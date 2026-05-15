#!/usr/bin/env python3
"""Validate all EA catalog files against JSON standards, meta files, metamodel, and cardinality."""

import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOGS_DIR = os.path.join(ROOT, "catalogs")
METAMODEL_PATH = os.path.join(ROOT, "metamodel.json")

errors = []

def e(msg):
    errors.append(msg)
    print(f"  ERROR: {msg}")

def load_json(path, label):
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as ex:
        e(f"{label}: Invalid JSON — {ex}")
    except FileNotFoundError:
        e(f"{label}: File not found")
    return None

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

# Cardinality → expected JSON type for the viaField
CARD_TYPE = {
    "one-to-one": "string",
    "many-to-one": "string",
    "one-to-many": "string",
    "many-to-many": "array",
}


def check_field_type(value, expected, field, eid):
    if expected == "array":
        if not isinstance(value, list):
            e(f"{eid}: Field '{field}' must be an array, got {type(value).__name__}")
    elif expected == "string":
        if value is not None and not isinstance(value, str):
            e(f"{eid}: Field '{field}' must be a string, got {type(value).__name__}")


def validate_catalog(catalog_name):
    d = os.path.join(CATALOGS_DIR, catalog_name)
    fp = os.path.join(d, f"{catalog_name}.json")
    mp = os.path.join(d, f"{catalog_name}-Meta.json")

    if not os.path.isdir(d):
        e(f"Catalog directory missing: {d}")
        return None

    entries = load_json(fp, f"{catalog_name}.json")
    meta = load_json(mp, f"{catalog_name}-Meta.json")

    if entries is None:
        return None
    if not isinstance(entries, list):
        e(f"{catalog_name}.json: top-level must be a JSON array")
        return None

    entity = entity_by_catalog.get(catalog_name)
    if entity is None:
        e(f"{catalog_name}: not defined in metamodel.json entityTypes")
        return None

    expected_prefix = ID_PREFIXES.get(catalog_name, "")
    fdefs = fields_by_entity.get(entity["name"], {})
    meta_fdefs = {f["name"]: f for f in meta["fields"]} if meta else {}

    # Cardinality map for this entity
    card_map = {}
    for rel in metamodel.get("relationships", []):
        if rel["source"] == entity["name"] and rel.get("viaField"):
            card_map[rel["viaField"]] = rel["cardinality"]

    for entry in entries:
        if not isinstance(entry, dict):
            e(f"{catalog_name}.json: entry is not an object: {entry}")
            continue

        eid = entry.get("id", f"<no-id-in-{catalog_name}>")

        if expected_prefix and not str(eid).startswith(expected_prefix):
            e(f"{eid}: ID does not start with expected prefix '{expected_prefix}'")

        for fn, fd in fdefs.items():
            if fd.get("required") and fn not in entry:
                e(f"{eid}: missing required field '{fn}' (metamodel)")

        for fn, fd in meta_fdefs.items():
            if fd.get("required") and fn not in entry:
                e(f"{eid}: missing required field '{fn}' (meta file)")

        for fn in entry:
            if fn not in fdefs:
                e(f"{eid}: unknown field '{fn}'")

        for fn, val in entry.items():
            if fn in fdefs:
                check_field_type(val, fdefs[fn]["type"], fn, eid)

        for fn, card in card_map.items():
            if fn in entry:
                wanted = CARD_TYPE.get(card)
                if wanted == "array" and not isinstance(entry[fn], list):
                    e(f"{eid}: field '{fn}' has cardinality {card} but is not an array")
                elif wanted == "string" and isinstance(entry[fn], list):
                    e(f"{eid}: field '{fn}' has cardinality {card} but is an array")

        if entity["name"] == "TechnologyStandard":
            val = entry.get("status")
            if val is not None:
                enum_def = ENUMS.get("TechnologyStandardStatus")
                if enum_def and val not in enum_def["values"]:
                    e(f"{eid}: status '{val}' invalid — allowed: {enum_def['values']}")

        if entity["name"] == "InfrastructureComponent":
            val = entry.get("type")
            if val is not None:
                enum_def = ENUMS.get("InfrastructureComponentType")
                if enum_def and val not in enum_def["values"]:
                    e(f"{eid}: type '{val}' invalid — allowed: {enum_def['values']}")

        if entity["name"] == "Permission":
            val = entry.get("accessLevel")
            if val is not None:
                enum_def = ENUMS.get("PermissionAccessLevel")
                if enum_def and val not in enum_def["values"]:
                    e(f"{eid}: accessLevel '{val}' invalid — allowed: {enum_def['values']}")

    return entries


# ── Pass 1: validate each catalog ──────────────────────────────────
all_by_id = {}

for cname in sorted(entity_by_catalog):
    entries = validate_catalog(cname)
    if entries:
        for ent in entries:
            eid = ent.get("id")
            if eid:
                all_by_id[eid] = (cname, ent)

# ── Pass 2: cross-reference validation ────────────────────────────
def check_ref(val, field, source_id):
    if val is None or val == "":
        return
    if val not in all_by_id:
        e(f"{source_id}: field '{field}' references '{val}' which does not exist")

for cname in sorted(entity_by_catalog):
    entity = entity_by_catalog.get(cname)
    if entity is None:
        continue
    fp = os.path.join(CATALOGS_DIR, cname, f"{cname}.json")
    entries = load_json(fp, f"{cname}.json (ref-pass)")
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

# ── Summary ────────────────────────────────────────────────────────
print()
print("=" * 60)
print(f"  Errors: {len(errors)}")
if errors:
    print("  VALIDATION FAILED")
    sys.exit(1)
else:
    print("  ALL CHECKS PASSED")
