# GUI - Saphir

> **Purpose**: central document for everything related to the user interface (UI) —
> principles, QML structure, screens, the system visual status, theming, and localization.
>
> **Related documents**:
> - [`../../specifications/workflow.md`](../../specifications/workflow.md) — the workflow → screen **contract** (§7 UI State Mapping,
>   §7.1 `SystemLoadingPanel`, §7.2 system visual status).
> - [`../design-rules.md`](../design-rules.md) — the GUI **design rules** (this document's §1).
> - [`qml-layer.md`](qml-layer.md) — the QML layer and the data models (the former `architecture.md` §3.4–3.5).
> - [`../../project-status.md`](../../project-status.md) — GUI rule-debt and feature backlog.
>
> Where a rule is *defined* in [`qml-layer.md`](qml-layer.md) and a mapping is a *workflow contract*, this
> document references them instead of duplicating; it centralises the UI-specific detail.

---

## 1. Design rules

The five GUI design rules are **defined** in [`../design-rules.md`](../design-rules.md) §1
(Saphir GUI design rules). One-line summary:

| # | Rule | One-line summary |
|---|------|------------------|
| 1.1 | **View-state rule (MVVM)** | Views are stateless projections of `SystemState`; no business conditionals in QML. |
| 1.2 | **One screen at a time** | At most one screen column per state; `SystemLoadingPanel` is an overlay. |
| 1.3 | **Form & responsiveness** | Responsive, input-agnostic; 8-inch touch tablet primary, desktop PC supported; no hard-coded tablet assumption. |
| 1.4 | **Input model** | Safecor virtual inputs; touch-first — cursor hidden by default, re-appears on first mouse movement. |
| 1.5 | **Form-factor selector** | `handheld` (medium screen + touch) drives the UI variant; currently forced `True`. |

Any deviation from a rule is **rule-debt**, tracked in
[`../../project-status.md`](../../project-status.md) (GUI backlog & rule-debt).

---

## 2. QML structure

| File | Role |
|------|------|
| `GUI/content/MainScreen.qml` | Window root; composes `MainScreenUi` + a top-level `Bindings`. Sets `imgBack` (background) and `backFilter.colorizationColor` (system status). |
| `GUI/content/MainScreenUi.ui.qml` | The layout: `TopBar`, language/theme menus, the **swappable content item** (three panels: `FilesSelectionPanel` / `AnalysisPanel` / `FilesCopyPanel`), `SystemLoadingPanel`, and all dialogs (`dlgConnectStorage`, `dlgAnalyseWholeStorage`, `dlgRestart`, `dlgShutdown`, `dlgSystemMustBeReset`, `SystemStateDialog`, `LogDialog`). |
| `GUI/content/Bindings.qml` | The **single indirection layer** between views and `ApplicationController`: scalar bindings (`ready`, `analysisReady`, `analyzing`, `systemState`, `nbClean`, `nbInfected`, `queueSize`, `remainingTimeInMinutes`, …), model bindings, and method bridges (`startStopAnalysis`, `reset`, `shutdown`, …). |
| `GUI/Components/Environment.qml` | **Theming singleton**: `theme` switches every color/image; exposes `handheld` and the system-status images (§5). |
| `GUI/Components/Constants.qml` | Theme ids, Material-icon codes, `Section` enum. |

**Data models** — all QML-facing list/table data is held in `QAbstractItemModel` subclasses
owned by `ApplicationController` and exposed as constant `QObject` properties (see
[`qml-layer.md`](qml-layer.md)):

| Model | Base | Role |
|-------|------|------|
| `SafecorInputFilesListModel` (+ `...ProxyModel`) | `QAbstractListModel` | source-disk file browser |
| `QueueListModel` (+ `...ProxyModel`) | `QAbstractListModel` | analysis queue + Clean/Infected/Other filters |
| `ComponentsModel` | `QAbstractTableModel` | component name/state list |
| `SystemInformationModel` | `QAbstractTableModel` | system info |
| `MessagesListModel` | `QAbstractItemModel` | message feed (hidden) |
| `LogListModel` | `QAbstractTableModel` | event journal |

---

## 3. Screens & state mapping

The per-state screen visibility is a **workflow contract** defined in
[`../../specifications/workflow.md` §7](../../specifications/workflow.md). The four screens:

- **File Selection** (`FilesSelectionPanel`) — browse the source disk, build the queue.
- **Analysis Panel** (`AnalysisPanel`) — progress, ETA, **pause**.
- **File Copy** (`FilesCopyPanel`) — copy progress, "insert a target" prompt.
- **Shutdown Dialog** — shutdown confirmation.

Plus the **`SystemLoadingPanel`** overlay (size/visibility driven by the workflow — see
[`../../specifications/workflow.md` §7.1](../../specifications/workflow.md)).

---

## 4. System visual status (Ready / Used / Dirty)

Beyond the per-state screens, the **whole application** carries a *visual status* of the system,
expressed through the **background image** (`imgBack`) and a **color filter** (`backFilter`). It
tells the user whether the system is clean, has been used, or has found a threat. It is
**orthogonal to the workflow states** (a derived visual, not a `SystemState`).

The contract (conditions, precedence, workflow relation) is in
[`../../specifications/workflow.md` §7.2](../../specifications/workflow.md). Summary:

| Visual status | Meaning | Condition (derived) | Image (light theme) | Color filter |
|---------------|---------|---------------------|---------------------|--------------|
| **Not ready** | boot | `!ready` | `dark.jpg` | `colorFilterNotReady` |
| **Ready** | operational, nothing scanned | `ready ∧ ¬used ∧ ¬infected` | `light_ready.png` | `colorFilterReady` |
| **Used** | a file read, no threat | `ready ∧ used ∧ ¬infected` | `light_used.png` | `colorFilterUsed` |
| **Dirty** — currently "Infected" in the code | an infected file detected | `ready ∧ infected` | `light_infected.png` | `colorFilterInfected` |

where `used = nbFinished > 0` and `infected = nbInfected > 0`. Precedence: **Dirty > Used >
Ready > Not ready**. A **Reset** returns the status to **Ready**.

> **Bug (D8)**: `Bindings.qml` computes `infected: nbInfected > 1` (should be `> 0`).

---

## 5. Theming

`Environment.qml` is the theming singleton. `theme` (default `Constants.dark`) switches every
color and image across `ThemeDark` / `ThemeLight` / `ThemeLowVisibility` / `ThemeWireframe`.

### 5.1 Themes

- `dark` (default)
- `light`
- `lowVisibility`
- `wireframe`

> **Default theme** (D1, resolved): **dark** (`Environment.qml`). Spec F7 updated to match.

### 5.2 System images

| Property | dark | light | lowVisibility |
|----------|------|-------|---------------|
| `backgroundImage` | `dark.jpg` | `light.jpg` | `dark.jpg` |
| `systemReadyImage` | `dark.jpg` | `light_ready.png` | `dark.jpg` |
| `systemUsedImage` | `dark.jpg` | `light_used.png` | `dark.jpg` |
| `systemInfectedImage` | `dark.jpg` | `light_infected.png` | `dark.jpg` |

### 5.3 Semantic colors (excerpts)

| Category | Colors |
|----------|--------|
| System status filter | `colorFilterNotReady`, `colorFilterReady`, `colorFilterUsed`, `colorFilterInfected` |
| File results | `colorClean`, `colorInfected`, `colorWaiting`, `colorRunning`, `colorSelected` |
| Feedback | `colorWarning`, `colorSuccess` |
| Classification | `colorNotProtected`, `colorRestricted`, `colorSecret`, `colorTopSecret` |
| Chrome | `colorDark`, `colorClear`, `colorControl`, `colorText`, `colorBorder`, `colorBg` |
| Controls | `colorButtonEnabled/Disabled`, `colorButtonTextEnabled/Disabled`, `colorPanelEnabled/Disabled`, `colorShadowEnabled/Disabled` |
| Icons | `colorIconFolder`, `colorIconFile` |

---

## 6. Localization

Bilingual **EN / FR**. `ApplicationController.language` + `__install_translations` /
`__translator` drive the UI language. The scan report is currently always rendered with the EN
template even though a FR template exists (**divergence D3**).

---

## 7. Rule-debt & backlog

- **Rule-debt** (deviations from the rules in §1, defined in
  [`../design-rules.md`](../design-rules.md)) and the **GUI feature backlog** are tracked in
  [`../../project-status.md`](../../project-status.md) (GUI backlog & rule-debt).
