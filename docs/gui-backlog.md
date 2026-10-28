# GUI backlog & rule-debt tracker

> **Purpose**: track (1) the **GUI feature backlog** and (2) **rule-debt** — anything in the
> QML layer that deviates from the GUI architecture rules and must be addressed in a future
> increment.
>
> The rules tracked here are defined in [`architecture.md`](architecture.md) §3.4:
> - **View-state rule (MVVM)** — views are stateless projections of `SystemState`; no business
>   logic in QML.
> - **Form & responsiveness rule** — responsive, input-agnostic views; 8-inch touch tablet
>   primary, desktop PC (keyboard + mouse) also supported.

## Rule-debt (deviations from GUI rules)

> Every deviation from a GUI rule is logged here. These are **debt** to be addressed in a
> future increment, not bugs to fix in the current scope.

### Entry format

```
### [YYYY-MM-DD] <short title>
- **Rule**: view-state | form/responsiveness | other
- **Where**: <file / component>
- **Description**: <what deviates and why it matters>
- **Proposed fix**: <how to address it in a future increment>
- **Status**: open | resolved
```

### [2026-10-28] Form-factor adaptation not implemented (`handheld` forced, no responsive layout)
- **Rule**: form/responsiveness
- **Where**: `GUI/.../Environment.qml` (`handheld`), `python/gui/src/Saphir/main.py` (`InputEventFilter`)
- **Description**: The cursor behaviour — hidden by default (touch-first) and re-appearing on
  first mouse movement — is **by design** (automatic environment discovery on top of Safecor's
  virtual-input abstraction) and **conforms** to the rule. The actual debt is that **form-factor
  adaptation is not implemented**: `handheld` is forced (always the medium/touch variant), so the
  interface does not yet adapt to the target — no small "PC" buttons, no per-screen-size layout,
  no keyboard navigation / hover / context menu. `handheld` exists to select the UI variant
  (small/medium/large screen, touch vs. keyboard+mouse) but is not yet wired to environment
  discovery or used to drive responsive layout.
- **Proposed fix**: wire `handheld` + screen size + input type to **environment discovery**
  (Safecor exposes virtual inputs transparently) so the UI can switch between a touch-optimised
  layout (large buttons) and a desktop layout (small buttons, hover, keyboard nav, context menu),
  keeping the single interface.
- **Status**: open

## Dependencies & packaging (to review)

> Tracking of the GUI VM dependencies: what is needed, what is bloat, and what the
> packaging (PyInstaller bundle) already handles.

### [2026-10-28] GUI dependencies cleanup — drop QtNetwork, document OpenGL deps
- **Type**: optimization / dependencies
- **Where**: `python/gui/saphir-gui.spec` (stripping filter + hiddenimports), `saphir-gui/APKBUILD`
- **Description**:
  - The PyInstaller spec **already strips** the unused Qt modules (Qt3D, QtCharts,
    QtMultimedia, QtWeb/WebEngine, QtSensors, QtSql, QtSvg, …) — so the **bundle**
    (`bundle="yes"`) is already much smaller than the *folder* mode measured in
    `docs/old/optimization.md` (1.1 GB).
  - **QtNetwork** is **still bundled** (it is a `hiddenimport` and not in the strip
    filter), but the GUI communicates over **MQTT (paho-mqtt)**, not QtNetwork →
    **candidate for removal** (verify the GUI still runs first; it may be a transitive
    load of QtQuick/QtQml).
  - **MESA + LLVM (~236 MB)** are **not** bloat: they are tied to **OpenGL hardware
    acceleration**, which is **needed on the target tablet** for GPU rendering → **keep**
    (only removable if we drop to software rendering).
- **Proposed fix**: remove `PySide6.QtNetwork` from `hiddenimports` and add it to the
  strip filter (test first); document MESA/LLVM as required for OpenGL in the tech-stack
  analysis.
- **Status**: open

## GUI feature backlog

> Future GUI features / enhancements, not yet scheduled.

_(none yet)_
