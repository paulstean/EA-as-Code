# Changelog

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
