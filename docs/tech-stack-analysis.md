# Tech-Stack & Memory Analysis — Saphir

> **Status**: Draft — to be discussed (decisions pending, §7)
> **Last updated**: 2026-10-28
> **Audience**: developers / maintainers deciding the tech stack before the refactor
> **Scope**: evaluate the GUI tech stack (PySide6 vs C++/Qt) and the system memory strategy under the target constraints (tablet 8–16 Go, Safecor multi-VM isolation, stateless goal). This document **collects the analysis and the pending decisions**; it is updated as each point (§7) is decided (§8).

---

## 1. Context & constraints

- **Target hardware**: tablet (primary), smartphone (future). **8 Go RAM** (typical), 16 Go (eventual).
- **Safecor**: strong isolation via **VMs** (one domain per component). The memory footprint is dominated by the **VMs**, not by the individual applications.
- **Stateless goal**: boot + install packages in RAM without modifying the disk (Alpine *diskless*) — but this is **very RAM-hungry**.
- **ClamAV**: ~**3 Go** (signatures + engine).
- **ESET**: **not available for Alpine** (not MUSL-linked) → it runs in a **minimal Debian LXC** inside an Alpine VM. This is a large, avoidable cost.

---

## 2. Current data

### 2.1 VM topology (`setup/packages/saphir/saphir/topology.json`)

| Domain | RAM | vCPU | temp disk | swap |
|--------|-----|------|-----------|------|
| `saphir-gui` | **1 200** | 0.2 | 1 024 | — |
| `saphir-av-clamav` | **3 000** | 0.8 | 4 096 | 1 024 |
| `saphir-av-eset` | **2 100** | 0.8 | 4 096 | 1 024 |
| **Total** | **6 300** | | | |

(+ dom0 / hypervisor / kernel on top.)

### 2.2 GUI footprint (`docs/old/optimization.md`)

- PySide6/QML GUI: **~389 MB RAM** (with MESA); ~99 MB base.
- **Two packaging modes** (`saphir-gui/APKBUILD`, `bundle` flag):
  - **Folder mode** (`bundle="no"`, what `optimization.md` measured): `py3-pyside6` is
    installed in the VM → the disk is **1.1 GB**, inflated by **unused** Qt modules:
    QtWebEngine (`libQt6WebEngineCore` 168 MB + locales/resources 34.9 + 12.5 MB),
    LLVM (153 MB), MESA/gallium (83 MB), multimedia (x265/avcodec/SvtAv1…), Qt3D/QtQuick3D.
  - **Bundle mode** (`bundle="yes"`, **current**): the app is a **PyInstaller bundle**.
    `safecor-gui-base` installs **only** the X server (no Qt). The Qt native libs are
    carried **inside the bundle**, and `saphir-gui.spec` **already strips** the unused
    Qt modules (Qt3D, QtCharts, QtMultimedia, QtWeb/WebEngine, QtSensors, QtSql, QtSvg,
    …). So the current bundle is **much smaller** than the 1.1 GB folder-mode figure.
    Two items are **not** stripped: **QtNetwork** (a `hiddenimport`) and **MESA/LLVM**
    (OpenGL — see below).

> **MESA/LLVM (~236 MB)** are **not** bloat: they back **OpenGL hardware acceleration**,
> required on the target tablet for GPU rendering. They are paid by **both** PySide6 and
> C++ and are **kept** (only removable with software rendering).

---

## 3. Question

Is **PySide6/Python** the right choice for the GUI, or should we move to a **compiled C++/Qt** app? Criteria: **memory**, **global performance**, **maintainability**.

---

## 4. Analysis

### 4.1 Memory (re-estimated, dependencies included, bundle mode)

> Sizes are orders of magnitude (the exact `.so` sizes vary); measure precisely when acting.

**A. Common to both stacks** (the minimal "cage" of the GUI VM, independent of Python/C++):

| Component | Disk |
|-----------|------|
| Required Qt libs (Core, Gui, Quick, Qml, Network, Widgets, QmlMeta/Models, QuickControls2, QuickEffects/Layouts/Shapes/Templates2, DBus, PDF) | ~150–200 MB |
| **MESA + LLVM** (OpenGL hardware acceleration, needed on the tablet) | ~236 MB |
| fontconfig + freetype + icu | ~60 MB |
| **Subtotal (paid either way)** | **~450–500 MB** |

**B. Stack-specific** (where Python/C++ differ):

| Component | PySide6 (bundle) | C++/Qt |
|-----------|------------------|--------|
| App binary | ~80–150 MB (Python interpreter + PySide6 bindings + shiboken) | ~10–50 MB |
| Python modules (weasyprint, jinja2, paho-mqtt, PIL, psutil, msgpack, …) | ~50–100 MB | 0 |
| **Report (PDF)** — WeasyPrint + fonttools + tinycss2 + pyphen | ~30–60 MB | C++ equivalent to develop, **or** WeasyPrint as a subprocess (→ same ~30–60 MB) |
| **Subtotal** | **~160–310 MB** | **~10–50 MB** (report reworked) / **~40–110 MB** (WeasyPrint subprocess) |

**C. Residual "unused" Qt still bundled**: **QtNetwork** (~15–25 MB) — kept (hiddenimport, not in the strip filter) although the GUI talks over **MQTT/paho-mqtt**, not QtNetwork → **to remove** (test first). See `gui-backlog.md`.

**D. Balance (GUI VM disk, current bundle mode)**:

| Configuration | Est. disk |
|---------------|-----------|
| PySide6 bundle **as-is** (unused modules already stripped) | **~600–800 MB** |
| PySide6 bundle + drop QtNetwork | **~575–775 MB** |
| C++/Qt stripped (report **reworked** in C++) | **~500–600 MB** |
| C++/Qt stripped (WeasyPrint **subprocess**) | **~575–750 MB** |

**PySide6 vs C++ gap: ~50–150 MB** (≈ 8–15 % of the GUI VM, ≈ 1–2 % of the total); it shrinks to **~20–50 MB** if the report stays WeasyPrint (subprocess). The initial 30–80 MB estimate was **low** (it omitted the Python modules + the PDF report).

Key point: **~450–500 MB of the GUI disk is common** (Qt + OpenGL/MESA/LLVM + fonts) and is **independent** of the language. The real levers are the **stripping** (mostly done; QtNetwork left) and the **big consumers** (ClamAV, ESET/LXC) — **not** the GUI language.

### 4.2 Global performance

- The bottleneck is the **scan** (ClamAV/ESET), not the GUI. The GUI is allocated **0.2 vCPU**, the AVs **0.8**.
- C++ would be **~100–300 ms faster at boot** and slightly more responsive, but this is **imperceptible for a kiosk**. System-level gain: **negligible**.

### 4.3 Maintainability

- The **whole codebase** (gui, libsaphir, viewer, AV controllers) is **Python**, communicating over **MQTT**. MVVM (signals/slots) is natural in Python.
- C++/Qt = a **full rewrite** of the GUI: high effort + risk, long compile cycle, low-level bugs, smaller dev pool.
- The **effort/benefit** ratio of C++ is **strongly unfavorable**: rewriting the whole GUI (and the PDF report, viewer, MQTT lib) to save **~1–2 % of the total** RAM.

---

## 5. The real memory levers (by impact)

1. **ClamAV (3 000 MB)** — the biggest. Levers: *FRESH* (minimal) signatures instead of *full*; load signatures **only during the scan**; **on-demand** (`clamdscan`) instead of a resident daemon.
2. **ESET/LXC (2 100 MB)** — the Debian LXC exists **only** because ESET is not MUSL-linked. Structural lever: replace ESET with a **2nd Alpine/MUSL-compatible engine** to reach the consensus (`ANTIVIRUS_NEEDED = 2`) **without the LXC** → removes ~2 100 MB + the LXC. **Biggest structural lever** (but loses ESET's detection quality).
3. **GUI VM** — the PyInstaller spec **already strips** the unused Qt modules (WebEngine, multimedia, Qt3D, …); only **QtNetwork** remains to drop (**~15–25 MB**, without changing the stack). **MESA/LLVM are kept** (OpenGL).
4. **Diskless mode** — if everything is in RAM (tmpfs/overlay), the footprint is huge. Weigh: **read-only base disk** + RAM overlay only for the session (or a persistent disk). It is a **goal**, not a hard requirement.

---

## 6. Preliminary recommendation

1. **Keep PySide6/Python** for the GUI (gain of C++ ≈ 1–2 % of the total, not worth a full rewrite).
2. **Finish the GUI stripping**: the PyInstaller spec **already** strips the unused Qt modules; only **QtNetwork** remains to drop (GUI uses MQTT). **Keep MESA/LLVM** (OpenGL hardware acceleration, needed on the tablet).
3. **Re-evaluate the 2nd engine**: an Alpine/MUSL-compatible engine instead of ESET/LXC is the **biggest structural lever** (~2 100 MB).
4. **Optimize ClamAV** (minimal signatures, on-demand).
5. **Weigh the diskless mode** against the statelessness goal.

---

## 7. Points to discuss (decisions pending)

Each point lists the decision, the options, the implications (memory / effort / quality), and a preliminary recommendation. Decisions are recorded in §8.

### D-T1 — GUI tech stack (PySide6 vs C++/Qt)
- **Options**: (a) keep PySide6/Python; (b) rewrite the GUI in C++/Qt.
- **Implications**: (a) no rewrite, keeps the Python ecosystem, **~50–150 MB** more than (b) (interpreter + Python modules + the PDF report); (b) ~50–150 MB saved, **full GUI rewrite** + reworking the **PDF report** (WeasyPrint has no trivial C++ equivalent) + the viewer + the MQTT lib, higher risk/effort. ~450–500 MB of the GUI disk (Qt + OpenGL/MESA/LLVM + fonts) is paid **either way**.
- **Preliminary**: **keep PySide6/Python** — the gain (~1–2 % of the total) is negligible vs the cost of a full rewrite.

### D-T2 — Strip the GUI VM
- **Options**: (a) keep the bundle as-is; (b) finish the stripping.
- **Implications**: the PyInstaller spec **already strips** the unused Qt modules (Qt3D, QtCharts, QtMultimedia, QtWeb/WebEngine, QtSensors, …), so the main bloat is **gone** in the current bundle. What remains: **QtNetwork** (~15–25 MB, to remove — GUI uses MQTT, not QtNetwork; test first) and **MESA/LLVM** (~236 MB, **keep** — OpenGL hardware acceleration, needed on the tablet). **Without changing the stack.**
- **Preliminary**: **drop QtNetwork** (verify the GUI still runs); **keep** MESA/LLVM (OpenGL). Tracked in `gui-backlog.md`.

### D-T3 — 2nd antivirus engine (ESET/LXC vs Alpine-compatible)
- **Options**: (a) keep ESET in the Debian LXC; (b) replace it with an **Alpine/MUSL-compatible** engine to reach the consensus without the LXC.
- **Implications**: (b) removes **~2 100 MB + the LXC** (biggest structural lever), but **loses ESET's detection quality**. (a) keeps ESET quality but pays the LXC cost. **Open question**: is there a 2nd MUSL-compatible engine available on Alpine with acceptable coverage?
- **Preliminary**: **open** — depends on the required detection quality. Needs a candidate-engine evaluation.

### D-T4 — ClamAV optimization
- **Options**: (a) current (full signatures, resident daemon); (b) *FRESH*/minimal signatures + **on-demand** (`clamdscan`) + load signatures **only during the scan**.
- **Implications**: (b) reduces the ClamAV VM footprint (toward the 3 000 MB) and the boot time. Risk: detection coverage (*FRESH* vs *full*) and scan latency.
- **Preliminary**: **optimize** (FRESH signatures, on-demand) — keep an eye on detection coverage.

### D-T5 — Diskless / stateless mode
- **Options**: (a) full diskless (everything in RAM); (b) **read-only base disk** + RAM overlay for the session; (c) persistent disk.
- **Implications**: (a) max statelessness, max RAM; (b) good compromise (RAM only for the session); (c) least stateless, least RAM.
- **Preliminary**: **open** — depends on the required statelessness level. Weigh the RAM cost against the goal.

---

## 8. Decision log

| ID | Decision | Date | Rationale |
|----|----------|------|-----------|
| — | *(none yet — to be filled as each D-Tx is decided)* | | |
