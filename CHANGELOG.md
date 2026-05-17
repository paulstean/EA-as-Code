# Changelog

## v0.1 (2026-05-17)

First public release. See [RELEASE_NOTES-v0.1.md](RELEASE_NOTES-v0.1.md) for full details.

### Added
- 12 TOGAF-aligned architecture catalogs (162 entries) including SecurityStandards with 25 ISO 27001:2022 controls
- `metamodel.json` with SecurityStandard entity type and SecurityStandardStatus enum
- Security standard compliance assessments on ApplicationComponents (Compliant/NonCompliant/PartiallyCompliant with rationale)
- ERT Project entities: External AI Consultancy, Azure Databricks, Incident/Weather data domains
- Multi-tab views with per-tab state persistence, dirty flag, and save/load prompt
- Text box annotations with text formatting (bold, font size S/M/L, alignment)
- Node field selection checkboxes in hover/right-click popover
- Node resize handle (drag bottom-right corner), persisted across refresh
- Zoom controls: +/- buttons with live zoom percentage display, zoom-to-fit button
- Resizable AI chat pane (drag left edge)
- Remove node from graph via popover button
- AI chat approval flow for adding/removing catalog entries on the diagram
- Chat log export (Markdown and HTML)
- Skills directory with agent skill files and validation
- Governance rules in `rules/*.md` with CI auto-evaluation

### Fixed
- vis-network console errors (invalid `zIndex`, `backgroundColor`, `maxVelocity` placement)
- Text box scaling with zoom (now uses CSS transform for stable sizing across zoom levels)
- Text box resize no longer forces full paragraph width
- Node field selection now per-node, not per-catalog
- Node position retention across refresh
- Default to light theme for first-time visitors
- Catalog names formatted with spaces between words (CamelCase → natural)

### Infrastructure
- GitHub Actions CI pipeline validating JSON, metamodel, cardinality, enums, skills
- 883 validation tests, zero errors
- All changes verified before commit
