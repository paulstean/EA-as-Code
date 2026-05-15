# Changelog

## v1.1.0 (2026-05-15)

### Added
- `visualiser.html` — single-file interactive EA graph browser (no build step, open in Chrome/Edge)
- `specification-visualiser.md` — full spec for the visualiser

### Visualiser Features
- Force-directed graph powered by vis-network with box-shaped nodes and arrow edges
- File System Access API (`showDirectoryPicker`) to load catalogs at runtime from local clone
- Catalog multi-select checkboxes with Select All / Deselect All
- Search/filter by name and description with dimmed non-matching nodes
- Node detail panel with resolved reference links (clickable cross-catalog navigation)
- Hover highlights connected nodes, dims the rest
- Dark/light theme toggle with localStorage persistence
- Empty canvas start — user builds the graph incrementally

## v1.0.0 (2026-05-15)

Initial release of EA-as-Code.

### Added
- 11 TOGAF-aligned architecture catalogs with synthetic seed data for an Electrical Distribution Utility
- `metamodel.json` defining entity types, relationships with cardinality, and enum constraints
- Per-catalog `-Meta.json` schema files with field definitions and relationship mappings
- GitHub Actions CI pipeline (`pr-review.yml`) with 4 stages: structural validation, diff analysis, Copilot rule assessment, PR comment
- Sample governance skill file in `rules/`
- Specification document (`specification.md`) detailing the full system design

### Catalogs
- BusinessUnits (8 entries), BusinessProcesses (7), BusinessActivities (18)
- DataDomains (7), DataEntities (22)
- ApplicationComponents (9), InformationFlows (12), InfrastructureComponents (8)
- BusinessUserGroups (9), Permissions (15), TechnologyStandards (10)

### Infrastructure
- Repository structure with catalog-per-directory layout
- All cross-references validated — zero orphaned IDs
