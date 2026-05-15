# EA-as-Code

Enterprise Architecture as Code — a git-based repository that stores an organisation's IT landscape as structured JSON catalogs. The `main` branch is the production architecture. Changes are proposed via branches and pull requests, where a GitHub Copilot agent governed by natural-language skill files assesses compliance before merge.

Aligned to **TOGAF** conventions. Aimed at **governance and clarity**, not infrastructure-level detail.

---
/
├── metamodel.json              # Full EA metamodel (11 entity types, relationships, enums)
├── specification.md            # Full system specification
├── specification-visualiser.md # Visualiser specification
├── visualiser.html             # Single-file graph visualiser (open in browser)
├── AGENTS.md                   # Instructions for AI coding agents
├── catalogs/
│   ├── BusinessUnits/          # +-Meta.json
│   ├── BusinessProcesses/
│   ├── BusinessActivities/
│   ├── DataDomains/
│   ├── DataEntities/
│   ├── ApplicationComponents/
│   ├── InformationFlows/
│   ├── InfrastructureComponents/
│   ├── BusinessUserGroups/
│   ├── Permissions/
│   └── TechnologyStandards/
├── rules/
│   └── *.md                    # Governance skill files (auto-discovered)
└── .github/
    └── workflows/
        └── pr-review.yml       # CI pipeline
```

Each catalog directory contains:
- **`<Catalog>.json`** — array of entries (the data)
- **`<Catalog>-Meta.json`** — schema, field descriptions, relationship definitions

---

## Catalogs (v1)

| Catalog | TOGAF Domain | Entries | Purpose |
|---|---|---|---|
| BusinessUnit | Business | 8 | Organisational units (Network Operations, Finance, etc.) |
| BusinessProcess | Business | 7 | End-to-end processes (Manage Network Assets, Respond to Outages, etc.) |
| BusinessActivity | Business | 18 | Steps within processes (Create Work Order, Dispatch Crew, etc.) |
| BusinessUserGroup | Business | 9 | User roles (Field Crew, Network Controller, etc.) |
| DataDomain | Data | 7 | Data classifications (Asset, Customer, Financial, etc.) |
| DataEntity | Data | 22 | Logical data entities (Transformer, Account, Meter Read, etc.) |
| ApplicationComponent | Application | 9 | Systems (SAP AM, ADMS, D365 CRM, Azure Data Lake, etc.) |
| InformationFlow | Application | 12 | Data flows between systems |
| InfrastructureComponent | Technology | 8 | Physical/virtual infrastructure (AKS cluster, SAP HANA DB, etc.) |
| Permission | Technology | 15 | Access rights (group-to-system mappings) |
| TechnologyStandard | Technology | 10 | Approved/trial/sunset/forbidden technologies |

The seed data models a mid-size **Electrical Distribution Utility** using Azure, SAP S/4HANA (Asset Management, Finance, HR), ADMS, Dynamics 365 CRM, and Dynamics 365 WMS. All cross-references are valid — zero orphaned IDs.

---

## How It Works

1. **Branch** — A contributor creates a feature branch from `main`
2. **Edit** — They directly edit JSON files in `catalogs/*/` to represent the proposed change
3. **PR** — They open a pull request to `main` with a description including:
   - What is changing and why
   - The project or initiative driving the change
   - Expected business benefits
4. **Review** — The CI pipeline runs automatically:
   - **Stage 1** — Structural validation (JSON is well-formed, matches schema)
   - **Stage 2** — Diff analysis (counts additions/modifications/removals per catalog)
   - **Stage 3** — AI agent reads all `rules/*.md` files and evaluates the PR against each rule
   - **Stage 4** — A summary comment is posted on the PR
5. **Merge** — The architecture team reviews and merges to `main`

---

## Setting Up the GitHub Agent (CI Pipeline)

### Prerequisites

- A GitHub repository with this content pushed
- A GitHub Copilot for Business or Copilot Enterprise license (required for the `github/copilot-code-review` action)

### Step 1: Enable Copilot Code Review

The workflow uses the `github/copilot-code-review@v2` action. This requires:

1. Navigate to your repository **Settings → Actions → General**
2. Scroll to **Workflow permissions** and select **Read and write permissions**
3. Under **Actions → Copilot**, ensure **Allow Copilot code review** is enabled

### Step 2: Verify `GITHUB_TOKEN` Permissions

The workflow declares these permissions in the workflow file itself:

```yaml
permissions:
  contents: read
  pull-requests: write
```

The `GITHUB_TOKEN` secret is automatically provided by GitHub Actions — no manual setup required.

### Step 3: Push to GitHub

```bash
git remote add origin <your-repo-url>
git push -u origin main
```

### Step 4: Open a Test PR

Create a branch, make a change to any catalog JSON file, and open a pull request. The workflow should trigger automatically and you'll see:

1. A check running called **EA Architecture Review**
2. A PR comment posted with the change summary and rule assessment

---

## EA Visualiser

A single-file HTML application that loads catalogs from the repo and renders them as an interactive force-directed graph. No build step, no server — just open in Chrome or Edge.

### How to Use

1. Clone the repo: `git clone <repo-url>`
2. Open `visualiser.html` in Chrome or Edge
3. Click **Open Repository** and select the cloned repo folder
4. Check catalogs in the sidebar to add nodes to the graph
5. Click any node to see its full details with resolved references

### Features

| Feature | Description |
|---|---|
| **Force-directed graph** | Nodes spring apart, connected ones cluster. Powered by vis-network |
| **Catalog selection** | Multi-select checkboxes. Add/remove entire catalogs with instant graph update |
| **Select All / Deselect All** | One-click toggle for all catalogs |
| **Search / filter** | Type to dim non-matching nodes by name or description |
| **Node detail panel** | Click a node to see all its fields with resolved reference links |
| **Reference navigation** | Click a resolved reference (e.g. "SAP S/4HANA") to jump to that node |
| **Hover highlight** | Hover a node to highlight connected nodes and dim the rest |
| **Dark / light theme** | Toggle in the header. Preference saved to localStorage |
| **Start empty** | Canvas is blank until you select catalogs — build the view incrementally |

---

## Writing Skill Files

Skill files are natural-language Markdown files in `rules/`. They are auto-discovered — every `.md` file in that directory becomes an active rule.

### Format

```markdown
### Rule: <title>

<one or more paragraphs describing the constraint.
Reference catalog fields using backticks.>

**Severity:** error | warning
```

### Example

```markdown
### Rule: Business Activity must belong to a single Business Process and a single Business User Group

A Business Activity entry must reference exactly one Business Process
(via `businessProcessId`) and exactly one Business User Group
(via `businessUserGroupId`). Every Business Activity in this PR must
satisfy this constraint.

**Severity:** error
```

### Guidelines

- Write rules in plain English — the agent interprets them using natural language
- Reference field names in backticks (e.g. \`technologyStandardId\`)
- Reference catalog names for clarity (e.g. "every Application Component should...")
- Use `error` severity for hard constraints, `warning` for recommendations
- Rules can be added, modified, or removed in any branch and take effect on the next PR

---

## Adding a New Catalog

1. Create a new directory under `catalogs/`
2. Add `<CatalogName>.json` with an array of entries
3. Add `<CatalogName>-Meta.json` with field definitions and relationships
4. Update `metamodel.json` to add the new entity type
5. Update the CI workflow's `catalogs` list in `.github/workflows/pr-review.yml`
6. Optionally add seed data and skill file rules

---

## Future Phases

| Phase | Description |
|---|---|
| **Natural Language Query** | Ask plain-English questions about the architecture |
| **Azure DevOps Port** | Port CI from GitHub Actions to Azure DevOps pipelines |
| **Impact Analysis** | Automated assessment of what else a change affects |
| **Change Approval Workflow** | Formal gates, scheduling, change advisory board routing |
