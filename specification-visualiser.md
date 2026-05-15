# EA Visualiser — Specification

A single-file HTML application (`visualiser.html`) that loads EA-as-Code catalogs from a local repository folder and renders them as an interactive force-directed graph. Users open the HTML file in Chrome or Edge, point it at their cloned repo, and explore the architecture visually.

Zero build step. Zero server. Git clone → open → browse.

---

## 1. Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Graph rendering | vis-network (CDN) | Force-directed physics, zoom/pan/drag, click/hover events, single dependency |
| File access | File System Access API (`showDirectoryPicker`) | Chrome/Edge only — acceptable per spec |
| Styling | CSS custom properties | Dynamic dark/light theme switching via `data-theme` attribute |
| Scripting | Vanilla ES6 | No build step, no bundler, no framework |
| Icons | Inline SVG | No icon library dependency |

---

## 2. File Location

```
/
├── visualiser.html              # Single self-contained file
├── specification-visualiser.md  # This document
├── catalogs/                    # Loaded at runtime via directory picker
├── metamodel.json
└── ...
```

The visualiser loads all data from the sibling `catalogs/` directories and `metamodel.json` through the File System Access API. It does not hardcode paths — the user selects the repo root folder at runtime.

---

## 3. UI Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  ⚡ EA Visualiser                                    [Theme]  │
├───────────────┬──────────────────────────────────────────────────┤
│  Controls     │                                                  │
│               │                                                  │
│  [📂 Open     │          Force-Directed Graph                    │
│   Repository] │                                                  │
│               │          (empty until catalogs selected)         │
│  Catalogs     │                                                  │
│  ┌──────────┐ │               ○─────○                            │
│  │ Select…   ▼│ │              /       \                          │
│  ├──────────┤ │             ○         ○                          │
│  │ ☑ Systems │ │              \       /                           │
│  │ ☐ Flows   │ │               ○─────○                            │
│  │ ☐ …       │ │                                                  │
│  └──────────┘ │                                                  │
│               │                                                  │
│  🔍 Filter    │                                                  │
│  [_________]  │                                                  │
│               │                                                  │
│  Legend       │                                                  │
│  ■ Systems    │                                                  │
│  ■ Flows      │                                                  │
│  ■ …          │                                                  │
│               │                                                  │
├───────────────┴──────────────────────────────────────────────────┤
│  📋 Node Detail — SAP Asset Management                 [✕]      │
│  ─────────────────────────────────────────────────────────       │
│  ID: app-001                                                     │
│  Catalog: ApplicationComponents                                  │
│  Description: SAP S/4HANA module for managing asset master        │
│  Technology Standard: SAP S/4HANA (ts-002) ✓                     │
│  Hosted on: SAP HANA Database (infra-003) ✓                      │
│  ─────────────────────────────────────────────────────────       │
│  Relationships (4):                                              │
│  → Azure Data Lake              sends flow-005                   │
│  ← SAP Finance                  receives flow-008                │
│  → ADMS                         sends flow-003                   │
│  ← Dynamics 365 WMS             receives flow-010                │
└──────────────────────────────────────────────────────────────────┘
```

The layout is a 2-column split. Left sidebar is fixed at 280px. Graph canvas fills the remainder. Node detail panel slides up from the bottom, ~240px tall, overlaid on the canvas.

---

## 4. Controls Panel (Left Sidebar)

### 4.1 Open Repository Button

- Styled button at the top of the sidebar: **📂 Open Repository**
- Calls `window.showDirectoryPicker({ mode: 'read', startIn: 'documents' })`
- On success:
  1. Recursively walk the selected directory for all files matching `catalogs/*/*.json` and `metamodel.json`
  2. Parse `metamodel.json` first to get the list of known catalog names
  3. Match remaining found JSON files against known catalog names (the file stem must match exactly, e.g. `ApplicationComponents.json`)
  4. Parse all matching catalog JSON files
  5. Populate the catalog multi-select and legend
  6. Show a success toast: *"Loaded N catalogs from {folder name}"*
  7. Graph remains empty — user selects catalogs next

### 4.2 Open Repository Button — States

| State | Visual |
|---|---|
| Idle | Normal button |
| Loading | Button disabled, text: "📂 Loading…" |
| Loaded | Button text: "📂 Reopen" |
| Error | Button text: "📂 Open Repository", error message below |

Error scenarios to handle:
- User cancels the picker (no-op, return to idle)
- `metamodel.json` not found in the selected folder
- Catalog JSON fails to parse (skip that catalog, warn user)
- Permission revoked (catch `SecurityError`, prompt user to re-select)

### 4.3 Catalog Multi-Select

- Custom-styled `<select multiple>` or checkbox panel
- Lists all catalogs that were found in the loaded repository
- Each entry shows:
  - Checkbox
  - Catalog name (e.g. "ApplicationComponents")
  - Entry count (e.g. "9")
  - Color swatch matching the node colour
- **Selecting a catalog**:
  - Adds all entries of that catalog type as nodes to the graph
  - Resolves and draws any edges that connect visible nodes
  - Physics re-stabilises
- **Deselecting a catalog**:
  - Removes all nodes of that catalog type from the graph
  - Removes all edges connected to those nodes
  - Physics re-stabilises
- A **"Select All"** and **"Deselect All"** shortcut below the list
- If no catalogs are loaded (repo not opened), show an empty state: *"Open a repository first"*

### 4.4 Search / Filter

- Text input with 🔍 icon
- Filters currently visible nodes by `name` and `description` fields (case-insensitive substring match)
- Matching nodes remain at full opacity
- Non-matching nodes are dimmed to `opacity: 0.10` — not removed from the graph
- Edges connected to dimmed nodes are also dimmed
- Clearing the search restores full opacity to all nodes
- Debounced at 150ms

### 4.5 Legend

- Auto-populated from the loaded catalog palette
- Each row:
  - Coloured square (same colour as node border)
  - Catalog name
  - Entry count in parentheses
- Only catalogs present in the loaded repo are shown
- Legend is updated when repository is loaded

### 4.6 Theme Toggle

- Positioned in the top-right of the header bar
- Button cycles between two states:
  - ☀️ (currently dark → switch to light)
  - 🌙 (currently light → switch to dark)
- Toggles `data-theme="dark"` / `data-theme="light"` on `<html>`
- vis-network options are updated to match: `network.setOptions({ nodes: { color: { ... } }, backgroundColor: ... })`
- Preferred theme is stored in `localStorage` and restored on page load

---

## 5. Graph Canvas

### 5.1 Initial State

- Empty canvas
- Centred text: *"Open a repository and select catalogs to begin"* (light grey, subtle)
- vis-network initialised but empty

### 5.2 Node Rendering

| Property | Value |
|---|---|
| Shape | `box` with `borderRadius: 6` |
| Width | Auto-sized to label text (vis-network default) |
| Background | Catalog colour, 15% opacity fill |
| Border | Catalog colour, full opacity, 2px width |
| Font | `{ color: var(--text-primary), size: 12, face: 'Segoe UI, sans-serif' }` |
| Shadow | Enabled with slight blur |

- Each node's `id` is the entry's `id` field
- Each node's `label` is the entry's `name` field
- Each node has `title` set to a concise hover tooltip string: *"{name} — {catalogType}"*
- Full entry data is stored in a separate `Map<nodeId, entryObject>` lookup table, not on the vis-network node. On click, the detail panel retrieves the entry by node ID from this map
- Each vis-network node stores its catalog type in a custom `group` property for programmematic filtering

### 5.3 Edge Rendering

| Property | Value |
|---|---|
| Arrows | `{ to: { enabled: true, scaleFactor: 0.8 } }` |
| Colour | Relationship type colour, `alpha: 0.4` |
| Width | 1.5px |
| Dashes | `false` for solid lines |
| Smooth | `{ type: 'curvedCW', roundness: 0.1 }` (avoids overlapping straight lines) |
| Hover width | 3px highlight |

- Each edge's `title` is set to the relationship description from `metamodel.json`
- Edges are only drawn between two nodes that are both currently visible in the graph
- When a catalog is deselected, all edges involving its nodes are removed

### 5.4 Physics Configuration

```js
physics: {
  enabled: true,
  solver: 'barnesHut',
  barnesHut: {
    gravitationalConstant: -800,
    centralGravity: 0.1,
    springLength: 150,
    springConstant: 0.01,
    damping: 0.09
  },
  stabilization: {
    iterations: 1000,
    updateInterval: 25
  },
  maxVelocity: 15,
  minVelocity: 0.75
}
```

- Physics auto-stabilises after each change (catalog add/remove, filter)
- Physics is disabled during user drag (vis-network default)
- `gravitationalConstant: -800` keeps nodes loosely packed without excessive white space
- `springLength: 150` and `springConstant: 0.01` produce short, flexible edges
- `centralGravity: 0.1` gently pulls disconnected clusters toward centre

### 5.5 Interaction

| Action | Result |
|---|---|
| Click on empty canvas | Deselect any selected node, close detail panel |
| Click on node | Open detail panel for that node |
| Double-click node | Zoom to node (fit viewport around it) |
| Hover node | Highlight connected nodes, dim non-connected |
| Scroll | Zoom in/out |
| Click + drag canvas | Pan |
| Click + drag node | Reposition node (physics disabled for that node until released) |

---

## 6. Node Detail Panel

### 6.1 Trigger

Clicking any node opens the detail panel at the bottom of the screen.

### 6.2 Content

| Section | Content |
|---|---|
| **Header** | Node name (large), catalog type badge (coloured), close ✕ button |
| **Fields** | Key-value list of all fields from the entry JSON |
| **References** | Fields that are reference IDs are resolved: show the referenced entry's name and catalog, not the raw ID. Clicking a resolved reference selects that node in the graph |
| **Relationships** | Two lists: **Outbound** (this node → others) and **Inbound** (others → this node). Each entry shows the direction arrow, the relationship description, and the target node name. Clicking a target node selects it and navigates to it |

### 6.3 Reference Resolution

Example: If the entry has `"owningBusinessUnitId": "bu-003"`, the detail panel displays:
```
Owning Business Unit: Finance (BusinessUnits)
```
If the referenced node's catalog is currently visible in the graph, the name is rendered as a clickable link. Clicking triggers `network.selectNodes(['bu-003'])` and pans to it.
If the referenced node's catalog is not visible, the name is displayed as plain text (dimmed, not clickable) — the user must select that catalog first to navigate to it.

### 6.4 Dismissal

- Click the ✕ button
- Click empty canvas space
- Press `Escape` key
- Clicking a different node replaces the current detail with the new one

---

## 7. Themes

### 7.1 Implementation

- CSS custom properties on `:root`, overridden by `[data-theme="dark"]` and `[data-theme="light"]`
- vis-network requires programmatic options update on theme switch

### 7.2 Dark Theme (default)

```css
--bg-primary: #1a1a2e;
--bg-secondary: #16213e;
--bg-card: #0f3460;
--text-primary: #e8e8e8;
--text-secondary: #8899b4;
--text-muted: #5a6a84;
--border: #2a2a4a;
--accent: #4fc3f7;
--shadow: rgba(0,0,0,0.4);
--hover-highlight: rgba(79, 195, 247, 0.15);
```

vis-network options:
```js
{
  nodes: {
    color: { background: catalogColor + '26', border: catalogColor },
    font: { color: '#e8e8e8' }
  },
  backgroundColor: '#1a1a2e'
}
```

### 7.3 Light Theme

```css
--bg-primary: #f5f7fa;
--bg-secondary: #ffffff;
--bg-card: #eef1f5;
--text-primary: #1a1a2e;
--text-secondary: #555577;
--text-muted: #9999bb;
--border: #d0d5e0;
--accent: #1976d2;
--shadow: rgba(0,0,0,0.1);
--hover-highlight: rgba(25, 118, 210, 0.1);
```

vis-network options:
```js
{
  nodes: {
    color: { background: catalogColor + '26', border: catalogColor },
    font: { color: '#1a1a2e' }
  },
  backgroundColor: '#f5f7fa'
}
```

### 7.4 Edge Colours (same for both themes)

| Relationship | Colour |
|---|---|
| Belongs to / Owned by | `#e67e22` |
| Performed by | `#2ecc71` |
| Supported by | `#3498db` |
| Uses Technology | `#9b59b6` |
| Hosted on | `#7f8c8d` |
| Sends information | `#e74c3c` |
| Receives information | `#e74c3c` |
| Carries / Contains | `#1abc9c` |
| Granted to / Applies to | `#e84393` |
| Self-referential | `#95a5a6` |

---

## 8. Data Flow

```
User clicks [Open Repository]
  → showDirectoryPicker()
  → User selects repo root folder
  → Walk directory recursively:
      → Find all files matching catalogs/*/<Catalog>.json
      → Find metamodel.json at root
  → Parse all JSON files
  → Build internal data model:
      → nodes = Map<id, { entry, catalogType }>
      → catalogs = Set of all found catalog types
      → relationships = from metamodel.json
  → Populate sidebar: catalog multi-select, legend
  → Graph remains empty

User checks a catalog checkbox
  → For each entry in that catalog:
      → Create vis-node with entry data
  → For each relationship in metamodel:
      → For each visible node of source type:
          → Read viaField
          → Find target node by ID
          → If target node is visible, create vis-edge
  → Physics stabilises

User clicks a node
  → Resolve all reference fields (look up referenced entries)
  → Build detail panel HTML
  → Show detail panel at bottom
  → On "resolved reference" click: network.selectNodes([targetId]), pan
```

---

## 9. Relationship Resolution Logic

For each relationship `R` in `metamodel.relationships`:

```
1. For each visible node N where N.catalogType == R.source:
2.   Let refValue = N.entry[R.viaField]
3.   If refValue is null/undefined: skip
4.   If refValue is an array (e.g. dataEntityIds):
5.     For each id in refValue:
6.       Find T in visible nodes where T.entry.id == id AND T.catalogType == R.target
7.       If T found: create edge N → T
8.   Else (scalar, e.g. technologyStandardId):
9.     Find T in visible nodes where T.entry.id == refValue AND T.catalogType == R.target
10.    If T found: create edge N → T
11. Self-referential (source == target): same logic, may create loops
```

Edge metadata:
```js
{
  from: N.id,
  to: T.id,
  title: R.description,
  arrows: 'to',
  color: { color: relationshipColor, highlight: relationshipColor },
  dashes: false
}
```

For self-referential relationships (BusinessUnit → BusinessUnit), edges where `N.id === refValue` (self-loops) are drawn as small loops above the node.

---

## 10. Performance Considerations

| Concern | Mitigation |
|---|---|
| Node count | ~125 max — well within vis-network capacity |
| Physics on add/remove | vis-network handles incrementally. Stabilisation limited to 500 iterations |
| JSON parse on load | ~25 small JSON files, total <500KB — sub-100ms parse |
| Filter dimming | vis-network `setOptions` for opacity — no re-render needed |
| Directory walk | Recursive `getEntries()` on File System Directory Handle. Async, ~50ms for this structure |

---

## 11. Palette — Catalog Colours

| Catalog | Hex | CSS Variable |
|---|---|---|
| BusinessUnits | `#e74c3c` | `--color-bu` |
| BusinessProcesses | `#e67e22` | `--color-bp` |
| BusinessActivities | `#f39c12` | `--color-ba` |
| BusinessUserGroups | `#2ecc71` | `--color-bug` |
| DataDomains | `#1abc9c` | `--color-dd` |
| DataEntities | `#3498db` | `--color-de` |
| ApplicationComponents | `#9b59b6` | `--color-app` |
| InformationFlows | `#34495e` | `--color-flow` |
| InfrastructureComponents | `#7f8c8d` | `--color-infra` |
| Permissions | `#e84393` | `--color-perm` |
| TechnologyStandards | `#00cec9` | `--color-ts` |

---

## 12. Out of Scope (v1)

| Feature | Rationale |
|---|---|
| Editing / saving changes | The visualiser is read-only — changes happen via git |
| Export to image | Browser right-click Save-as works natively |
| Full-text search across all fields | Name + description filter is sufficient for navigation |
| Multi-repo / branch comparison | Future enhancement |
| Touch / mobile support | Desktop Chrome/Edge only |
| Animated node add/remove | vis-network lacks smooth transitions for addition |
| Three interchangeable renderers | vis-network is the sole renderer. Switching adds complexity without benefit |
