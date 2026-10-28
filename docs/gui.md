# GUI - Saphir

> **Purpose**: central document for everything related to the user interface (UI) —
> principles, QML structure, screens, the system visual status, theming, and localization.
>
> **Related documents**:
> - [`workflow-rules.md`](workflow-rules.md) — the workflow → screen **contract** (§7 UI State Mapping,
>   §7.1 `SystemLoadingPanel`, §7.2 system visual status).
> - [`architecture.md`](architecture.md) — the QML layer and the data models (§3.4–3.5).
> - [`gui-backlog.md`](gui-backlog.md) — GUI rule-debt and feature backlog.
>
> Where a rule is *defined* in `architecture.md` and a mapping is a *workflow contract*, this
> document references them instead of duplicating; it centralises the UI-specific detail.

---

## 1. Principles

### 1.1 View-state rule (MVVM)

The QML views are **stateless projections of the workflow**. What is shown — the active panel,
enabled/disabled buttons, open dialogs, editable fields — is **derived directly from
`SystemState`** and the published bindings. A view must not *decide* visibility or enablement
with its own business conditionals: bind it to a property that already encodes the state
(e.g. `enabled: viewModel.canStartAnalysis`) and push any non-trivial derivation into the
controller/ViewModel, exposed as a single property. Only **trivially presentational** logic
with no workflow meaning (hover highlight, slider clamping) may live in a view. This keeps the
UI deterministic and testable by driving `SystemState` alone. *(Defined in
[`architecture.md`](architecture.md) §3.4.)*

### 1.2 One screen at a time

At most **one** of the screen columns (File Selection, Analysis Panel, File Copy, Shutdown
Dialog) is visible per state. The `SystemLoadingPanel` is an **overlay** (not a screen), so it
may be shown on top of a screen. *(Contract in [`workflow-rules.md`](workflow-rules.md) §7.)*

### 1.3 Form & responsiveness rule

The views must be **responsive** and **input-agnostic**. The **primary deployment target** is an
**8-inch touch tablet** (touch-first), but the application must also be usable on a **desktop PC
with keyboard and mouse**. For now a **single interface** serves both, with different input
handling; it must not hard-code the tablet assumption. The layout must tolerate a range of screen
sizes so the UI can later **specialise** per target (large screen / desktop, and smartphone if it
becomes viable) **without a redesign**. Any view that hard-codes a fixed size, assumes
touch-only, or breaks on a non-tablet form factor is **rule-debt** (see
[`gui-backlog.md`](gui-backlog.md)). *(Defined in [`architecture.md`](architecture.md) §3.4.)*

### 1.4 Input model (Safecor virtual inputs)

Safecor abstracts physical input devices (a USB vector of attack) and exposes **virtual inputs**
to the product, injecting the signals transparently. On top of that the app is **touch-first**:
the cursor is hidden by default and **re-appears on first mouse movement**
(`InputEventFilter` switches `Qt.BlankCursor` → `Qt.ArrowCursor`) — i.e. **automatic environment
discovery**, not a configured flag. *(From [`architecture.md`](architecture.md) §3.2.)*

### 1.5 Form-factor selector (`handheld`)

`handheld` (`Environment.qml`) means **medium screen + touch** (a mouse may still be attached);
it is meant to drive the UI variant (small "PC" buttons vs. large "touch" buttons, per-screen-size
layout). It is currently **forced** (always `True`) and not yet wired to environment discovery —
form-factor adaptation is open rule-debt (see [`gui-backlog.md`](gui-backlog.md)).

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
[`architecture.md`](architecture.md) §3.5):

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
[`workflow-rules.md` §7](workflow-rules.md). The four screens:

- **File Selection** (`FilesSelectionPanel`) — browse the source disk, build the queue.
- **Analysis Panel** (`AnalysisPanel`) — progress, ETA, **pause**.
- **File Copy** (`FilesCopyPanel`) — copy progress, "insert a target" prompt.
- **Shutdown Dialog** — shutdown confirmation.

Plus the **`SystemLoadingPanel`** overlay (size/visibility driven by the workflow — see
[`workflow-rules.md` §7.1](workflow-rules.md)).

---

## 4. System visual status (Prêt / Utilisé / Sale)

Beyond the per-state screens, the **whole application** carries a *visual status* of the system,
expressed through the **background image** (`imgBack`) and a **color filter** (`backFilter`). It
tells the user whether the system is clean, has been used, or has found a threat. It is
**orthogonal to the workflow states** (a derived visual, not a `SystemState`).

The contract (conditions, precedence, workflow relation) is in
[`workflow-rules.md` §7.2](workflow-rules.md). Summary:

| Visual status | Meaning | Condition (derived) | Image (light theme) | Color filter |
|---------------|---------|---------------------|---------------------|--------------|
| **Not ready** | boot | `!ready` | `dark.jpg` | `colorFilterNotReady` |
| **Ready** (Prêt) | operational, nothing scanned | `ready ∧ ¬used ∧ ¬infected` | `light_ready.png` | `colorFilterReady` |
| **Used** (Utilisé) | a file read, no threat | `ready ∧ used ∧ ¬infected` | `light_used.png` | `colorFilterUsed` |
| **Dirty** (Sale) — currently "Infected" | an infected file detected | `ready ∧ infected` | `light_infected.png` | `colorFilterInfected` |

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

> **Divergence (D1)**: the spec (F7) default theme is **light**, the implementation default is
> **dark** (`Environment.qml`).

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

- **Rule-debt** (deviations from the rules in §1) and the **GUI feature backlog** are tracked in
  [`gui-backlog.md`](gui-backlog.md).
