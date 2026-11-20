# Report Controller

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Reference**: `python/gui/src/Saphir/Saphir/report_controller.py` (templates in `python/gui/src/Saphir/Saphir/templates/`)

## Purpose

`ReportController` (QObject) generates the **PDF scan report** as evidence of the scan: it builds a data dict from the analysis results, renders it with a **Jinja2** template (`scan_report_en.html`), and writes the PDF with **WeasyPrint** (`write_pdf`). (It always uses the EN template, even though a FR template exists — see the coverage audit, divergence D3.)

## Key API

| Member | Role |
|--------|------|
| `get_report_filename()` | the base name of the generated report (`"Scan report.pdf"`) |
| `get_report_filepath()` | the full path where the report is written (temp dir) |
| `_render_html(...)` | builds the template data: per-file analysis details (filepath, fingerprint, per-engine results) + summary (scan result label, start/end datetime, analyzed/clean/infected/copied/copy-failure counts, equipment id, storage name, Safecor & Saphir versions, antivirus list) |
| `_write_pdf(html_content, out_filepath)` | WeasyPrint rendering to PDF |
| `make_report(...)` | renders and writes the report, then emits `reportGenerated` (or `reportFailed`) |

## Key signals

| Signal | Payload | Meaning |
|--------|---------|---------|
| `reportGenerated` | — | the PDF is ready in the temp dir |
| `reportFailed` | `str` | the report could not be generated (workflow state `ReportFailed`) |

After `reportGenerated`, `ApplicationController` copies the report **and the event journal** to the target disk via `system/disks/create_file` (see [../../development/protocol.md](../../development/protocol.md)).

## Links

- Workflow state `GeneratingReport` / `ReportFailed`: [../../specifications/workflow.md](../../specifications/workflow.md)
- Report feature (F6): [../../specifications/features.md](../../specifications/features.md)
- Per-file data (fingerprint, results): [../overview.md](../overview.md) §6
- Communication topics: [../../development/protocol.md](../../development/protocol.md)
