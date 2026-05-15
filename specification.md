# Enterprise Architecture as Code — Specification

## 1. Overview

A git-based Enterprise Architecture (EA) repository that stores an organisation's IT landscape as structured JSON catalogs. The `main` branch represents the production architecture. Changes are proposed via branches and pull requests, where AI agents governed by natural-language rules assess compliance before merge.

The system is aligned to TOGAF conventions and treats architecture-as-code — aimed at governance and clarity, not infrastructure-level detail.

---

## 2. Repository Structure

```
/
├── metamodel.json                          # Full EA metamodel (TOGAF-aligned)
├── catalogs/
│   ├── BusinessUnits/
│   │   ├── BusinessUnits.json              # Data
│   │   └── BusinessUnits-Meta.json         # Metadata / schema
│   ├── BusinessProcesses/
│   │   ├── BusinessProcesses.json
│   │   └── BusinessProcesses-Meta.json
│   ├── BusinessActivities/
│   │   ├── BusinessActivities.json
│   │   └── BusinessActivities-Meta.json
│   ├── DataDomains/
│   │   ├── DataDomains.json
│   │   └── DataDomains-Meta.json
│   ├── DataEntities/
│   │   ├── DataEntities.json
│   │   └── DataEntities-Meta.json
│   ├── ApplicationComponents/
│   │   ├── ApplicationComponents.json
│   │   └── ApplicationComponents-Meta.json
│   ├── InformationFlows/
│   │   ├── InformationFlows.json
│   │   └── InformationFlows-Meta.json
│   ├── InfrastructureComponents/
│   │   ├── InfrastructureComponents.json
│   │   └── InfrastructureComponents-Meta.json
│   ├── BusinessUserGroups/
│   │   ├── BusinessUserGroups.json
│   │   └── BusinessUserGroups-Meta.json
│   ├── Permissions/
│   │   ├── Permissions.json
│   │   └── Permissions-Meta.json
│   └── TechnologyStandards/
│       ├── TechnologyStandards.json
│       └── TechnologyStandards-Meta.json
├── rules/
│   └── *.md                                # Governance skill files (auto-discovered)
└── .github/
    └── workflows/
        └── pr-review.yml                   # CI pipeline
```

### 2.1 File Naming Convention

Each catalog directory is named in UpperCamelCase plural form. Inside:

| File | Purpose |
|---|---|
| `<CatalogName>.json` | Array of catalog entries (the data) |
| `<CatalogName>-Meta.json` | Metadata: field descriptions, schema constraints, tags |

---

## 3. Catalog Definitions (v1 — 11 Catalogs)

### 3.1 BusinessUnit
Represents an organisational unit (division, department, branch).

**Minimum fields:** `id`, `name`, `parentBusinessUnitId` (optional), `description`

**Relationships:**
- A Business Unit may contain child Business Units (self-referential)
- A Business Unit owns Business Processes

### 3.2 BusinessProcess
An end-to-end process that delivers value.

**Minimum fields:** `id`, `name`, `owningBusinessUnitId`, `description`

**Relationships:**
- Belongs to exactly one Business Unit
- Composed of one or more Business Activities

### 3.3 BusinessActivity
A discrete step within a Business Process.

**Minimum fields:** `id`, `name`, `businessProcessId`, `businessUserGroupId`, `supportedByApplicationComponentIds` (optional array), `description`

**Relationships:**
- Belongs to exactly one Business Process
- Performed by exactly one Business User Group
- May be supported by zero or more Application Components

### 3.4 DataDomain
A high-level classification of data (e.g. Customer, Product, Finance).

**Minimum fields:** `id`, `name`, `owningBusinessUnitId`, `description`

**Relationships:**
- Owned by exactly one Business Unit
- Contains one or more Data Entities

### 3.5 DataEntity
A logical data entity within a Data Domain.

**Minimum fields:** `id`, `name`, `dataDomainId`, `description`

**Relationships:**
- Belongs to exactly one Data Domain
- May be produced or consumed by Application Components (via Information Flows)

### 3.6 ApplicationComponent
A software application or system.

**Minimum fields:** `id`, `name`, `technologyStandardId` (optional), `infrastructureComponentId` (optional), `description`

**Relationships:**
- May use a Technology Standard
- Sends/receives Information Flows
- Hosted on exactly one Infrastructure Component (or zero for external/SaaS)

### 3.7 InformationFlow
A data flow between two Application Components.

**Minimum fields:** `id`, `name`, `sourceApplicationComponentId`, `targetApplicationComponentId`, `dataEntityIds` (array), `description`

**Relationships:**
- Links exactly one source Application Component to exactly one target Application Component
- Carries one or more Data Entities

### 3.8 InfrastructureComponent
Physical or virtual infrastructure (server, database, network device, cloud service).

**Minimum fields:** `id`, `name`, `type` (e.g. "Server", "Database", "KubernetesCluster"), `technologyStandardId` (optional), `description`

**Relationships:**
- May use a Technology Standard
- Hosts Application Components

### 3.9 BusinessUserGroup
A group of users with a common role or function.

**Minimum fields:** `id`, `name`, `description`

**Relationships:**
- Performs Business Activities
- Granted Permissions

### 3.10 Permission
A right or access level assigned to a Business User Group for an Application Component.

**Minimum fields:** `id`, `name`, `businessUserGroupId`, `applicationComponentId`, `accessLevel` (e.g. "Read", "Write", "Admin"), `description`

**Relationships:**
- Granted to exactly one Business User Group
- Applies to exactly one Application Component

### 3.11 TechnologyStandard
An approved, trialled, sunset, or forbidden technology.

**Minimum fields:** `id`, `name`, `category` (e.g. "ProgrammingLanguage", "Database", "CloudService"), `status` (enum: `Approved`, `Trial`, `Sunset`, `Forbidden`), `description`

**Relationships:**
- Referenced by Application Components and Infrastructure Components

---

## 4. Metamodel (`metamodel.json`)

Located at the repository root. Defines the full EA data model. Structure:

```json
{
  "metamodelVersion": "1.0",
  "togafAlignment": {
    "framework": "TOGAF 9.2",
    "architectureDomains": ["Business", "Data", "Application", "Technology"]
  },
  "entityTypes": [
    {
      "name": "ApplicationComponent",
      "catalog": "ApplicationComponents",
      "togafDomain": "Application",
      "description": "A software application or system",
      "fields": [
        { "name": "id", "type": "string", "required": true, "description": "Unique identifier" },
        { "name": "name", "type": "string", "required": true, "description": "Display name" },
        { "name": "technologyStandardId", "type": "string", "required": false, "description": "Technology standard used" },
        { "name": "infrastructureComponentId", "type": "string", "required": false, "description": "Host infrastructure component" },
        { "name": "description", "type": "string", "required": false, "description": "Description of the component" }
      ]
    }
  ],
  "relationships": [
    {
      "source": "ApplicationComponent",
      "target": "TechnologyStandard",
      "cardinality": "many-to-one",
      "viaField": "technologyStandardId",
      "description": "An Application Component may use a Technology Standard"
    },
    {
      "source": "ApplicationComponent",
      "target": "InfrastructureComponent",
      "cardinality": "many-to-one",
      "viaField": "infrastructureComponentId",
      "description": "An Application Component is hosted on an Infrastructure Component"
    },
    {
      "source": "ApplicationComponent",
      "target": "InformationFlow",
      "cardinality": "one-to-many",
      "viaField": "sourceApplicationComponentId",
      "description": "An Application Component may send Information Flows"
    },
    {
      "source": "ApplicationComponent",
      "target": "InformationFlow",
      "cardinality": "one-to-many",
      "viaField": "targetApplicationComponentId",
      "description": "An Application Component may receive Information Flows"
    },
    {
      "source": "BusinessActivity",
      "target": "BusinessProcess",
      "cardinality": "many-to-one",
      "viaField": "businessProcessId",
      "description": "A Business Activity belongs to one Business Process"
    },
    {
      "source": "BusinessActivity",
      "target": "BusinessUserGroup",
      "cardinality": "many-to-one",
      "viaField": "businessUserGroupId",
      "description": "A Business Activity is performed by one Business User Group"
    },
    {
      "source": "BusinessActivity",
      "target": "ApplicationComponent",
      "cardinality": "many-to-many",
      "viaField": "supportedByApplicationComponentIds",
      "description": "A Business Activity may be supported by Application Components"
    },
    {
      "source": "BusinessProcess",
      "target": "BusinessUnit",
      "cardinality": "many-to-one",
      "viaField": "owningBusinessUnitId",
      "description": "A Business Process is owned by one Business Unit"
    },
    {
      "source": "DataDomain",
      "target": "BusinessUnit",
      "cardinality": "many-to-one",
      "viaField": "owningBusinessUnitId",
      "description": "A Data Domain is owned by one Business Unit"
    },
    {
      "source": "DataEntity",
      "target": "DataDomain",
      "cardinality": "many-to-one",
      "viaField": "dataDomainId",
      "description": "A Data Entity belongs to one Data Domain"
    },
    {
      "source": "InformationFlow",
      "target": "ApplicationComponent",
      "cardinality": "many-to-one",
      "viaField": "sourceApplicationComponentId",
      "description": "An Information Flow originates from one Application Component"
    },
    {
      "source": "InformationFlow",
      "target": "ApplicationComponent",
      "cardinality": "many-to-one",
      "viaField": "targetApplicationComponentId",
      "description": "An Information Flow terminates at one Application Component"
    },
    {
      "source": "InformationFlow",
      "target": "DataEntity",
      "cardinality": "many-to-many",
      "viaField": "dataEntityIds",
      "description": "An Information Flow carries Data Entities"
    },
    {
      "source": "InfrastructureComponent",
      "target": "TechnologyStandard",
      "cardinality": "many-to-one",
      "viaField": "technologyStandardId",
      "description": "An Infrastructure Component may use a Technology Standard"
    },
    {
      "source": "Permission",
      "target": "BusinessUserGroup",
      "cardinality": "many-to-one",
      "viaField": "businessUserGroupId",
      "description": "A Permission is granted to one Business User Group"
    },
    {
      "source": "Permission",
      "target": "ApplicationComponent",
      "cardinality": "many-to-one",
      "viaField": "applicationComponentId",
      "description": "A Permission applies to one Application Component"
    },
    {
      "source": "BusinessUnit",
      "target": "BusinessUnit",
      "cardinality": "one-to-many",
      "viaField": "parentBusinessUnitId",
      "description": "A Business Unit may contain child Business Units"
    }
  ],
  "enums": {
    "TechnologyStandardStatus": {
      "values": ["Approved", "Trial", "Sunset", "Forbidden"],
      "description": "Lifecycle status of a technology standard"
    },
    "InfrastructureComponentType": {
      "values": ["Server", "Database", "NetworkDevice", "KubernetesCluster", "LoadBalancer", "Firewall", "Storage", "CloudService", "Other"],
      "description": "Type of infrastructure component"
    },
    "PermissionAccessLevel": {
      "values": ["Read", "Write", "Admin", "FullControl"],
      "description": "Access level granted by a permission"
    }
  }
}
```

---

## 5. Initial Seed Data

The repository's initial commit must pre-populate every catalog with realistic synthetic data representing a typical **Electrical Distribution Utility**. This serves as the production baseline on `main` from which all future changes branch.

### 5.1 Domain Context

A mid-size electrical distribution utility operating in a regulated market. It manages ~500,000 metered connections across urban, suburban, and rural areas. It operates a distribution network of poles, wires, transformers, and substations.

### 5.2 Core Systems in Scope

| System | Role | Technology |
|---|---|---|
| **SAP ECC / S/4HANA** | Asset Management (AM), Financials (FI), Human Resources (HR) | SAP |
| **ADMS** | Advanced Distribution Management System — real-time network monitoring, outage management, switching | Specialised OT |
| **CRM** | Customer relationship management, billing inquiries, service requests | Dynamics 365 |
| **WMS** | Warehouse management — materials, inventory, logistics | Dynamics 365 |
| **Azure Cloud** | Hosting infrastructure for ADMS, CRM, WMS, data platforms, integrations | Microsoft Azure |

### 5.3 Synthetic Data Guidance per Catalog

| Catalog | Data to include |
|---|---|
| **BusinessUnit** | `Network Operations`, `Asset Management`, `Finance`, `Human Resources`, `Information Technology`, `Customer Service`, `Warehouse & Logistics`, `Executive` |
| **BusinessProcess** | `Manage Network Assets`, `Process Customer Billing`, `Respond to Outages`, `Procure & Inventory Materials`, `Manage Financial Ledger`, `Recruit & Onboard Staff`, `Maintain Customer Accounts` |
| **BusinessActivity** | ~2-4 activities per Business Process (e.g. for "Respond to Outages": `Detect Outage via ADMS`, `Dispatch Crew`, `Restore Supply`, `Notify Customers`) |
| **DataDomain** | `Asset`, `Customer`, `Financial`, `Employee`, `Network Topology`, `Meter Data`, `Materials & Inventory` |
| **DataEntity** | ~2-4 entities per Data Domain (e.g. for "Asset": `Transformer`, `Pole`, `Cable Segment`, `Substation`; for "Customer": `Account`, `Premise`, `Meter`, `Service Request`) |
| **ApplicationComponent** | `SAP Asset Management`, `SAP Finance`, `SAP Human Resources`, `ADMS`, `Dynamics 365 CRM`, `Dynamics 365 WMS`, `Azure Data Lake`, `Azure Integration Bus`, `Corporate Portal` |
| **InformationFlow** | ~8-12 flows connecting the above systems (e.g. `CRM → SAP Finance` carries `Customer Billing Data`; `ADMS → CRM` carries `Outage Notifications`; `SAP AM → ADMS` carries `Asset Register Updates`) |
| **InfrastructureComponent** | ~6-10 components (e.g. `ADMS Production Cluster` — AKS, `CRM App Service` — Azure App Service, `SAP HANA Database`, `Data Lake Storage` — Azure Data Lake Gen2, `Integration Gateway` — Azure API Management) |
| **BusinessUserGroup** | `Field Crew`, `Asset Engineer`, `Network Controller`, `Customer Service Representative`, `Finance Analyst`, `HR Coordinator`, `Warehouse Operator`, `IT Administrator`, `Executive Leadership` |
| **Permission** | ~10-15 permissions mapping groups to systems with access levels (e.g. `Field Crew` has `Write` access to `SAP Asset Management` for work orders; `Network Controller` has `Admin` access to `ADMS`; `Customer Service Rep` has `Read` access to `SAP Finance` for billing inquiries) |
| **TechnologyStandard** | `Azure` (Approved), `SAP S/4HANA` (Approved), `Dynamics 365` (Approved), `ADMS Platform` (Approved), `PostgreSQL` (Trial), `Oracle Database` (Sunset), `Legacy Mainframe` (Forbidden), `Kubernetes` (Approved), `Terraform` (Approved), `Python` (Approved) |

### 5.4 Data Quality Rules

- Every `id` field must use a consistent scheme (e.g. `bu-001`, `app-001`, `flow-001`)
- Every reference field (e.g. `businessProcessId`, `dataDomainId`) must point to an `id` that exists in the target catalog
- No orphaned references in the initial seed
- Descriptions must be realistic prose (1-2 sentences), not placeholder text

## 6. Per-Catalog Metadata File (`*-Meta.json`)

Each `*-Meta.json` file contains:

```json
{
  "catalogName": "ApplicationComponents",
  "description": "Software applications and systems in the organisation",
  "togafDomain": "Application",
  "fields": [
    {
      "name": "id",
      "type": "string",
      "required": true,
      "description": "Unique identifier for the application component"
    },
    {
      "name": "name",
      "type": "string",
      "required": true,
      "description": "Display name of the application component"
    }
  ],
  "relationships": [
    {
      "targetCatalog": "TechnologyStandards",
      "type": "optionalRef",
      "field": "technologyStandardId",
      "description": "The technology standard this component uses"
    }
  ],
  "tags": []
}
```

---

## 7. Skill Files (`rules/*.md`)

Governance rules written as natural-language Markdown files. Discovered by convention — every `.md` file in `rules/` is a skill.

### 7.1 Format

```markdown
### Rule: <title>

<one or more paragraphs describing the constraint in natural language.
May reference catalog fields by name. May reference relationships
between entity types.>

**Severity:** error | warning
```

### 7.2 Example

```markdown
### Rule: Business Activity must belong to a single Business Process and a single Business User Group

A Business Activity entry must reference exactly one Business Process
(via `businessProcessId`) and exactly one Business User Group
(via `businessUserGroupId`). Every Business Activity in this PR must
satisfy this constraint.

**Severity:** error
```

### 7.3 Discovery

All `.md` files in `rules/` are sourced automatically. No manifest required. Files can be added, modified, or removed in any branch and become active on the next PR CI run.

---

## 8. CI Pipeline (GitHub Actions)

**File:** `.github/workflows/pr-review.yml`

**Trigger:** Pull requests opened, reopened, or synchronized against `main`.

### 8.1 Stage 1 — Structural Validation

- Validate all modified JSON files are well-formed
- Validate each JSON file against its corresponding `*-Meta.json` schema (field types, required fields)
- Validate `metamodel.json` remains consistent
- Fail the job if structural validation errors exist

### 8.2 Stage 2 — Diff Analysis

- Compute a structured diff of all changes across catalog files
- Generate a summary: count of additions, modifications, and deletions per catalog
- Detect added/modified entries and their full content

### 8.3 Stage 3 — Rule Assessment (AI Agent)

- A single GitHub Copilot agent reads all `rules/*.md` files
- The agent receives the structured diff and full contents of changed entries
- The agent evaluates each rule against the changes
- For each rule: pass, fail, or not applicable
- For each failure: provide a clear explanation referencing the specific entry and field

### 8.4 Stage 4 — PR Comment

Post a single PR comment containing:

```
## Architecture Review

### Change Summary

| Catalog | Added | Modified | Removed |
|---|---|---|---|
| ApplicationComponents | 2 | 1 | 0 |
| TechnologyStandards | 0 | 1 | 0 |
| ... | | | |

### Rule Assessment

| Rule | Status | Details |
|---|---|---|
| Business Activity must belong... | ✅ Pass | |
| New components must use approved tech | ❌ Fail | `AcmeApp (ApplicationComponents)` references `tech-XYZ` which is not in TechnologyStandards |
| ... | | |

### Overall: ❌ Changes require revision
```

### 8.5 Required Authentication

| Mechanism | Purpose |
|---|---|
| `GITHUB_TOKEN` | Authenticates the Copilot agent API calls within the workflow |

---

## 9. Branch Workflow

1. Contributor creates a feature branch from `main`
2. Contributor directly edits JSON files in `catalogs/*/`
3. Contributor opens a Pull Request to `main`
4. PR description must include:
   - **Change description** — what is changing and why
   - **Project name** — which initiative/project drives this change
   - **Business benefits** — expected outcome
5. CI pipeline triggers automatically
6. AI agent posts assessment comment on the PR
7. Architecture team reviews the PR and either:
   - Requests changes (contributor updates the branch)
   - Approves and merges to `main`

---

## 10. Future Phases (Out of Scope for v1)

| Phase | Description |
|---|---|
| **Visualisation Dashboard** | Web UI to browse catalogs, view relationship graphs, explore the architecture |
| **Natural Language Query** | Ask questions about the architecture in plain English (e.g. "Which systems handle customer data?") |
| **Azure DevOps Port** | Port the CI pipeline from GitHub Actions to Azure DevOps pipelines |
| **Change Approval Workflow** | Formal approval gates, change advisory board routing, scheduled change windows |
| **Impact Analysis** | Automated impact assessment showing what else is affected by a change |

---

## 11. Glossary

| Term | Definition |
|---|---|
| **Catalog** | A collection of homogeneous architecture items (e.g. all Application Components) |
| **Metamodel** | The model that describes the structure of the architecture model itself |
| **Skill File** | A Markdown file containing a natural-language governance rule |
| **Structural Validation** | Checking JSON files are well-formed and match their schema |
| **Rule Assessment** | AI-powered evaluation of changes against governance rules |
| **EA** | Enterprise Architecture |
| **TOGAF** | The Open Group Architecture Framework |

---

## 12. Appendix — TOGAF Domain Mapping

| Catalog | TOGAF Domain | ADM Phase |
|---|---|---|
| BusinessUnit | Business Architecture | Phase B |
| BusinessProcess | Business Architecture | Phase B |
| BusinessActivity | Business Architecture | Phase B |
| BusinessUserGroup | Business Architecture | Phase B |
| DataDomain | Data Architecture | Phase C |
| DataEntity | Data Architecture | Phase C |
| ApplicationComponent | Application Architecture | Phase C |
| InformationFlow | Application Architecture | Phase C |
| InfrastructureComponent | Technology Architecture | Phase D |
| Permission | Technology Architecture + Security | Phase D |
| TechnologyStandard | Technology Architecture | Phase D |
