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
- GUI VM disk: **1.1 GB** — inflated by **unused** dependencies pulled by `py3-pyside6`:
  - **QtWebEngine** (`libQt6WebEngineCore` 168 MB) + locales/resources (34.9 + 12.5 MB)
  - **LLVM** (`libLLVM` 153 MB)
  - **MESA / gallium** (83 MB)
  - **Multimedia** (`libx265` 18.8, `libavcodec` 15.7, `libSvtAv1Enc` 6.5, …)
  - **Qt3D / QtQuick3D** (3.4 MB, …)

---

## 3. Question

Is **PySide6/Python** the right choice for the GUI, or should we move to a **compiled C++/Qt** app? Criteria: **memory**, **global performance**, **maintainability**.

---

## 4. Analysis

### 4.1 Memory

- The GUI is **not** the dominant consumer: the GUI VM (1 200 MB) is **2.5× smaller than ClamAV** (3 000 MB) and the GUI **application itself** is only **~389 MB** — a third of its VM. There is headroom.
- C++/Qt would remove the **Python interpreter + shiboken** overhead (**~30–80 MB**). That is **~3–6 % of the GUI VM** and **~0.5 % of the total**. Negligible.
- The **Qt libraries** (the bulk of the GUI footprint) are **the same** in Python and C++ — they are **not** saved by switching to C++.

### 4.2 Global performance

- The bottleneck is the **scan** (ClamAV/ESET), not the GUI. The GUI is allocated **0.2 vCPU**, the AVs **0.8**.
- C++ would be **~100–300 ms faster at boot** and slightly more responsive, but this is **imperceptible for a kiosk**. System-level gain: **negligible**.

### 4.3 Maintainability

- The **whole codebase** (gui, libsaphir, viewer, AV controllers) is **Python**, communicating over **MQTT**. MVVM (signals/slots) is natural in Python.
- C++/Qt = a **full rewrite** of the GUI: high effort + risk, long compile cycle, low-level bugs, smaller dev pool.
- The **effort/benefit** ratio of C++ is **strongly unfavorable**: rewriting the whole GUI to save ~0.5 % of total RAM.

---

## 5. The real memory levers (by impact)

1. **ClamAV (3 000 MB)** — the biggest. Levers: *FRESH* (minimal) signatures instead of *full*; load signatures **only during the scan**; **on-demand** (`clamdscan`) instead of a resident daemon.
2. **ESET/LXC (2 100 MB)** — the Debian LXC exists **only** because ESET is not MUSL-linked. Structural lever: replace ESET with a **2nd Alpine/MUSL-compatible engine** to reach the consensus (`ANTIVIRUS_NEEDED = 2`) **without the LXC** → removes ~2 100 MB + the LXC. **Biggest structural lever** (but loses ESET's detection quality).
3. **GUI VM bloat** — **strip** the unused dependencies (QtWebEngine, MESA, multimedia, Qt3D, LLVM) → saves disk + RAM **without changing the stack**.
4. **Diskless mode** — if everything is in RAM (tmpfs/overlay), the footprint is huge. Weigh: **read-only base disk** + RAM overlay only for the session (or a persistent disk). It is a **goal**, not a hard requirement.

---

## 6. Preliminary recommendation

1. **Keep PySide6/Python** for the GUI.
2. **Strip** the GUI VM (WebEngine, MESA, multimedia, Qt3D, LLVM).
3. **Re-evaluate the 2nd engine**: an Alpine/MUSL-compatible engine instead of ESET/LXC is the **biggest structural lever** (~2 100 MB).
4. **Optimize ClamAV** (minimal signatures, on-demand).
5. **Weigh the diskless mode** against the statelessness goal.

---

## 7. Points to discuss (decisions pending)

Each point lists the decision, the options, the implications (memory / effort / quality), and a preliminary recommendation. Decisions are recorded in §8.

### D-T1 — GUI tech stack (PySide6 vs C++/Qt)
- **Options**: (a) keep PySide6/Python; (b) rewrite the GUI in C++/Qt.
- **Implications**: (a) no rewrite, keeps the Python ecosystem, ~30–80 MB more than (b); (b) ~30–80 MB saved, **full GUI rewrite**, higher risk/effort.
- **Preliminary**: **keep PySide6/Python** — the gain is negligible vs the cost.

### D-T2 — Strip the GUI VM
- **Options**: (a) keep all `py3-pyside6` dependencies; (b) strip the unused ones (QtWebEngine, MESA, multimedia, Qt3D, LLVM).
- **Implications**: (b) saves ~0.5 GB disk + RAM in the GUI VM, **without changing the stack**. Risk: breaking the GUI if a stripped dependency is actually used — the **minimal dependency set must be verified** first.
- **Preliminary**: **strip** (verify the minimal dependency set first).

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
