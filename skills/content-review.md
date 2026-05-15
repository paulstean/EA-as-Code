---
name: content-review
description: Review catalog entries for offensive language, unsuitable topics, and compliance with content standards.
---

# Content Review Skill

Review EA catalog entries for content quality, professional tone, and adherence to organisational content standards.

## Principles

- **Professional Tone**: All descriptions must be professional and objective. Avoid emotional, charged, or colloquial language. Descriptions should read as if written for a formal architecture document.

- **Respectful Content**: No derogatory, discriminatory, mocking, or otherwise inappropriate references — whether about individuals, groups, technologies, or vendors.

- **Suitable Topics**: Content must relate to enterprise architecture concerns only. No political statements, religious references, off-topic subject matter, or personal commentary.

- **Constructive Descriptions**: Every entry should be informative and useful to an architect or stakeholder. Descriptions that are trivial, circular, dismissive, or placeholder-like should be flagged.

## Usage

Ask the coding agent: "Load the content-review skill and review all catalog changes in this PR." The agent will inspect every modified entry across all 11 catalogs and report violations against the principles above.
