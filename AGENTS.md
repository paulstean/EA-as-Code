# AGENTS.md — Instructions for Coding Agents

This file contains instructions for AI coding agents working in the EA-as-Code repository.

## Repository Overview

EA-as-Code stores an organisation's enterprise architecture as structured JSON catalogs. The `main` branch is production. Changes come via branches and PRs evaluated by AI agents against `rules/*.md` skill files.

TOGAF-aligned. Governance and clarity, not infrastructure-level detail.

## Repository Structure

```
metamodel.json              # Always check this first for the canonical schema
catalogs/<Catalog>/
  <Catalog>.json            # Array of entries
  <Catalog>-Meta.json       # Schema, field defs, relationships
rules/*.md                  # Governance rule files (auto-evaluated by CI)
skills/*.md                 # Agent skill files (loaded on demand by coding agents)
.github/
  workflows/validate.yml    # CI: runs on push/PR to main
  scripts/
    validate_catalogs.py    # Validates JSON, meta, metamodel, cardinality, refs
    validate_skills.py      # Validates skill file metadata
    validate_all.py         # Runs both validation suites
```

## 11 Catalogs (v1)

| Catalog | File Prefix | ID Prefix | Key Relations |
|---|---|---|---|
| BusinessUnit | BusinessUnits | `bu-` | owns BusinessProcess, DataDomain |
| BusinessProcess | BusinessProcesses | `bp-` | belongs to BusinessUnit, composed of BusinessActivities |
| BusinessActivity | BusinessActivities | `ba-` | belongs to BusinessProcess, performed by BusinessUserGroup |
| BusinessUserGroup | BusinessUserGroups | `bug-` | performs BusinessActivity, granted Permission |
| DataDomain | DataDomains | `dd-` | owned by BusinessUnit, contains DataEntities |
| DataEntity | DataEntities | `de-` | belongs to DataDomain |
| ApplicationComponent | ApplicationComponents | `app-` | uses TechnologyStandard, hosted on InfrastructureComponent |
| InformationFlow | InformationFlows | `flow-` | source/target ApplicationComponent, carries DataEntities |
| InfrastructureComponent | InfrastructureComponents | `infra-` | uses TechnologyStandard, hosts ApplicationComponents |
| Permission | Permissions | `perm-` | grants BusinessUserGroup access to ApplicationComponent |
| TechnologyStandard | TechnologyStandards | `ts-` | status: Approved/Trial/Sunset/Forbidden |

## Making Changes

### Edit Existing Catalog

1. Find the catalog JSON file under `catalogs/<Catalog>/<Catalog>.json`
2. Add/modify entries in the JSON array
3. Use the ID prefix convention shown above
4. All reference fields must point to existing IDs (verify before committing)
5. Check `metamodel.json` for the canonical field definitions

### Add New Catalog

1. Create `catalogs/<NewCatalog>/<NewCatalog>.json`
2. Create `catalogs/<NewCatalog>/<NewCatalog>-Meta.json`
3. Add the entity type and relationships to `metamodel.json`

### Add Governance Rule

1. Create `rules/<descriptive-name>.md`
2. Format:
   ```markdown
   ### Rule: <title>
   <constraint in natural language, field names in backticks>
   **Severity:** error | warning
   ```
3. No manifest registration needed — auto-discovered

## Conventions

- **IDs**: `<prefix>-NNN` e.g. `app-001`, `bu-008`, `flow-012`
- **Descriptions**: 1-2 sentences, realistic prose, no placeholder text
- **No orphaned references**: every `*Id` field must resolve to an existing entry
- **All changes must be valid JSON**: arrays at the top level of every catalog file

## Skills

Skills in `skills/*.md` provide specialized instructions that coding agents can load on demand at the user's direction. They are separate from `rules/*.md` governance rules, which are auto-evaluated by CI.

### Skill Format

Each skill file uses YAML frontmatter with required fields:

```markdown
---
name: <kebab-case-name>
description: <one-line description of when to use this skill>
---

# <Title>

<full instructions in markdown>
```

### Add a Skill

1. Create `skills/<kebab-case-name>.md`
2. Add YAML frontmatter with `name` and `description`
3. The `name` field must match the filename slug (without `.md`)
4. Write instructions in markdown below the frontmatter

### Use a Skill

Ask the coding agent to load a skill by name. The agent will load the instructions and follow them for the current task.

## Before Committing

1. Run all validation scripts: `python3 .github/scripts/validate_all.py`
2. Write descriptive commit messages following conventional commits: `feat:`, `fix:`, `docs:`, `rule:`, `chore:`

## Verification

A validation script at `.github/scripts/validate_catalogs.py` checks all 11 catalogs for JSON validity, schema conformance against meta files and `metamodel.json`, cardinality rules, enum values, and cross-reference resolution. An additional script at `.github/scripts/validate_skills.py` validates skill metadata in `skills/*.md`. Run `validate_all.py` before committing to ensure all suites pass with zero errors.
