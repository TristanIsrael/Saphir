# 0010 — PySide6/Python GUI tech stack (no C++ rewrite)

> **Status**: Accepted (2026-10-28)
> **Source**: tech-stack-analysis.md §8 — D-T1

## Context

Criteria evaluated: **memory**, **global performance**, **maintainability**, for a kiosk GUI on a tablet (8–16 Go RAM). The whole codebase (gui, libsaphir, viewer, AV controllers) is Python communicating over MQTT, and MVVM (signals/slots) is natural in Python.

## Decision

**Keep PySide6/Python** for the GUI — no rewrite in C++/Qt.

## Consequences

- C++ would save only **~50–150 MB** (~1–2 % of the total RAM): ~450–500 MB of the GUI disk (Qt + OpenGL/MESA/LLVM + fonts) is **paid either way**, and the system-level performance gain is negligible for a kiosk.
- It would cost a **full rewrite** of the GUI **and** the PDF report (WeasyPrint has no trivial C++ equivalent), the viewer, and the MQTT lib.
- The real memory levers are elsewhere: GUI stripping ([0011](0011-gui-vm-qt-network-strip.md)), the ESET LXC ([0012](0012-keep-eset-debian-lxc.md)), ClamAV ([0013](0013-clamav-optimization.md)), and the stateless redesign ([0014](0014-stateless-volatile-encrypted-disks.md)).
