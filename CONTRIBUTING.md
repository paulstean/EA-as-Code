# Contributing

## Workflow

1. Create a feature branch from `main`
2. Make changes to the relevant catalog JSON files
3. Open a Pull Request to `main`
4. Ensure the PR description includes:
   - **Change description** — what is changing and why
   - **Project name** — which initiative or project drives this change
   - **Business benefits** — expected outcome
5. The CI pipeline runs automatically and an AI agent posts an assessment
6. Address any rule failures flagged by the agent
7. Request review from the architecture team

## Branch Naming

Use descriptive branch names with a prefix:

```
feat/add-databricks-instances
fix/correct-adms-tech-standard
docs/update-readme
rule/add-new-constraint
```

## JSON Conventions

### IDs
Use consistent prefixed identifiers:

| Catalog | Prefix | Example |
|---|---|---|
| BusinessUnits | `bu-` | `bu-001` |
| BusinessProcesses | `bp-` | `bp-001` |
| BusinessActivities | `ba-` | `ba-001` |
| DataDomains | `dd-` | `dd-001` |
| DataEntities | `de-` | `de-001` |
| ApplicationComponents | `app-` | `app-001` |
| InformationFlows | `flow-` | `flow-001` |
| InfrastructureComponents | `infra-` | `infra-001` |
| BusinessUserGroups | `bug-` | `bug-001` |
| Permissions | `perm-` | `perm-001` |
| TechnologyStandards | `ts-` | `ts-001` |

### Reference Integrity

Every reference field (`businessProcessId`, `dataDomainId`, etc.) must point to an existing `id` in the target catalog. The CI pipeline checks this.

### Descriptions

Write realistic, informative descriptions — not placeholder text. Each description should be 1-2 sentences explaining the purpose of the entry.

## Adding a New Catalog

1. Create a new directory under `catalogs/<CatalogName>/`
2. Add `<CatalogName>.json` — an array of entries
3. Add `<CatalogName>-Meta.json` — field definitions, relationships, tags
4. Update `metamodel.json`:
   - Add the entity type to `entityTypes[]` with all fields
   - Add any new relationships to `relationships[]`
   - Add any new enums to `enums`
5. Update the `catalogs` list in `.github/workflows/pr-review.yml`
6. Add seed data entries

## Adding a Skill File

1. Create a `.md` file in `rules/`
2. Use the format:

```markdown
### Rule: <title>

<constraint description in natural language>

**Severity:** error | warning
```

3. Reference catalog field names with backticks
4. The rule is auto-discovered — no manifest registration needed

## Pull Request Checklist

Before opening a PR, verify:
- [ ] All JSON files are well-formed and pass `python3 -m json.tool`
- [ ] All IDs follow the naming convention
- [ ] All cross-references are valid (no orphaned IDs)
- [ ] The PR description contains change description, project name, and business benefits
- [ ] Descriptions are realistic and informative
- [ ] If adding a new catalog, `metamodel.json` is updated
