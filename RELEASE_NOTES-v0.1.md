# EA-as-Code v0.1 — Initial Release

**Date:** 2026-05-17

The first public release of EA-as-Code: a git-based repository for storing and visualising an organisation's enterprise architecture as structured JSON catalogs, governed by TOGAF conventions.

---

## What's Included

### 12 Architecture Catalogs (162 entries)

| Catalog | Domain | Entries |
|---|---|---|
| BusinessUnit | Business | 8 |
| BusinessProcess | Business | 7 |
| BusinessActivity | Business | 18 |
| BusinessUserGroup | Business | 10 |
| DataDomain | Data | 9 |
| DataEntity | Data | 26 |
| ApplicationComponent | Application | 10 |
| InformationFlow | Application | 15 |
| InfrastructureComponent | Technology | 8 |
| Permission | Technology | 16 |
| TechnologyStandard | Technology | 10 |
| SecurityStandard | Technology | 25 |

All cross-references validated — zero orphaned IDs.

### EA Visualiser (`visualiser.html`)

Single-file interactive graph browser with no build step.

**Graph & Navigation**
- Force-directed graph with box-shaped nodes and arrow edges (vis-network)
- Catalog multi-select with collapsible sidebar and Select All / Deselect All
- Search/filter by name and description with dimmed non-matching nodes
- Node detail panel with resolved reference links (cross-catalog navigation)
- Hover highlights connected nodes, dims the rest
- Dark/light theme toggle with localStorage persistence
- Zoom in/out buttons with live zoom percentage display
- Zoom to fit button
- Physics sliders (repulsion, gravity, spring, damping, max velocity, edge curvature)

**Multi-Tab Views**
- Open multiple independent graph views as tabs
- Per-tab persistence of visible nodes, node positions, text boxes, and physics settings
- Dirty-flag tracking with save/load prompt on close
- Save/load tab state to JSON files
- Session restore via localStorage

**Text Box Annotations**
- Create text boxes via right-click on the canvas
- Drag to reposition, resize handles, contenteditable text
- Text formatting: bold, font size (S/M/L), alignment (left/center/right)
- Position and font scale correctly with zoom via CSS transform

**Node Customisation**
- Per-node field checkboxes in hover/right-click popover (choose which fields appear on a node)
- Node resize handle (drag bottom-right corner to resize)
- Persisted node size constraints across refresh
- Remove node from graph via popover button
- Hidden related nodes shown in popover with click-to-add

**Compliance Visualisation**
- Security standard compliance assessments (Compliant / NonCompliant / PartiallyCompliant)
- Each assessment includes a descriptive rationale

### AI Chat Server (`ea-chat-server.py`)

- Local Ollama integration with SSE streaming
- Model selection dropdown with mid-session switching
- Read-only text-based tool protocol (`[[READ:]]`, `[[GET:]]`, `[[SEARCH:]]`)
- Chat logging (Markdown and HTML export)
- AI can add/remove catalog entries on the diagram via approval flow

### CI/CD Pipeline

- Structural validation: JSON syntax, metamodel conformance, ID prefix convention
- Cross-reference and cardinality checks
- Enum value validation
- Skill metadata validation
- Runs on every push/PR to `main` via GitHub Actions

### Infrastructure

- `metamodel.json` — canonical schema defining 12 entity types, relationships, and enums
- `rules/*.md` — governance rules auto-evaluated by CI
- `skills/*.md` — agent skill files with YAML frontmatter validation
- `AGENTS.md` — instructions for AI coding agents
- All 883 validation tests pass

### Seed Data

Models a mid-size Electrical Distribution Utility with:
- SAP S/4HANA (Asset Management, Finance, HR)
- ADMS (Advanced Distribution Management System)
- Dynamics 365 (CRM, Warehouse Management)
- Azure (Data Lake, Integration Bus, Databricks, AKS)
- ERT Project entities (External AI Consultancy, Incident/Weather data)
- 25 ISO 27001:2022 security controls across Organizational, People, Physical, and Technological themes

---

## How to Use

```bash
# Clone the repository
git clone <repo-url>
cd EA-as-Code

# Start the AI chat server (serves visualiser + chat API)
python3 ea-chat-server.py

# Open http://localhost:8765/ in Chrome or Edge
```

## Validation

```bash
python3 .github/scripts/validate_all.py
```
