# Saphir — Features and NFR Specification

> **Status**: Draft v1
> **Last updated**: 2026-10-27
> **Usage**: Reference document for refactoring the Saphir codebase.

---

## Cross-cutting technical note

**Safecor: disks = partitions.** There is no distinction between a physical disk and a partition. A physical disk with N partitions produces N "disk" entries in the Safecor messages. The GUI treats each entry as an individually addressable partition.

---

## 1. Features

### F1 — Media detection and analysis mode selection

**Objective**: Detect the connection of a storage media and ask the user for the desired analysis mode.

**Behavior**:

- The system monitors the `DISK_STATE` events emitted by Safecor.
- A storage media can contain **multiple partitions**. Safecor sends one message per partition, each message representing a "disk". There is no distinction between disk and partition at the GUI level.
- The **first media** connected becomes the **source**.
- The **second media** connected becomes the **target**.
- If the disk is disconnected **before** the user has made their choice, the system returns to the initial state (waiting for a media).
- All media types are treated identically.
- The mode choice is **irreversible** without a reset.

**Target handling**:

- The second media can be inserted **at any time** (before, during or after the analysis).
- The system **notes** it immediately (disk name recorded).
- The **copy is triggered automatically** only when the analysis is finished **and** a target is available.
- If the target is inserted **after** the end of the analysis, the copy starts immediately.

**User interaction**:

- Upon detection of the source media, a dialog is displayed: "Scan the whole media?"
  - **Accept** → `AnalyseWholeSource` mode (full analysis of all partitions)
  - **Cancel** → `AnalyseSelection` mode (the user manually selects the files)

**Backlog**:

- `[bug]` "Scan all" mode: verify that all partitions of the media are properly analyzed (today only the root `/` of the first disk is requested).
- `[feature]` Allow the user to undo their mode choice without a reset.

---

### F2 — File navigation and selection (selection mode)

**Objective**: Allow the user to navigate the tree of the source media and build the analysis queue.

**Behavior**:

- The user navigates the tree via the file browser.
- The user can **switch partition** in the browser (via a selector). Switching partition **does not reset** the queue.
- The selection can be a **file** or a **folder**.
  - **File**: immediately added to the analysis queue.
  - **Folder**: the list of files is requested from Safecor **recursively**. Each received file is immediately added to the queue.
- The interface shows the selected files and folders with their checkbox enabled.
- The user can **deselect** (remove from the queue) a file or a folder at any time before starting the analysis.
- The user can select files **on each partition** and the queue accumulates.

**Constraints**:

- **No concurrent enqueue**: if a folder is being enqueued (file list pending), a new folder selection must wait for the previous one to finish. A wait queue is needed to serialize the requests.
- **No limit** on size or number of files in the queue.
- **Locked queue**: once the analysis has started, the queue can no longer be modified.

**Backlog**:

- `[feature]` Mechanism for a full queue drain (clear queue).

---

### F3 — Antivirus analysis

**Objective**: Analyze each file in the queue with all antivirus engines and determine the consensus.

**Trigger**:

- The user manually triggers the analysis (button).
- The queue is **locked** at that point.

**Copy to the repository (precondition)**:

- Before analysis, the file is copied from the source media to a **local repository**.
- The copy is triggered **file by file**, at the moment the file is to be analyzed.
- The antivirus needs the file available in the repository to analyze it.

**Parallelism** (objective: maximize resource utilization):

- Multiple **files** are analyzed in parallel (repository capacity, tied to the number of CPU cores).
- For a given file, all **antivirus engines** analyze in parallel.

**Consensus**:

- A file is considered **analyzed** when all engines have returned their result.
- The file **status** is ternary:
  - `Clean`: all engines declare the file clean
  - `Infected`: at least one engine declares the file infected
  - `Error`: an engine or the copy returns an error
- The **appearance** (GUI display) is binary:
  - `Clean`: status = clean
  - `Not clean`: status = infected **or** error
- Only `Clean` files will be copied to the target media (F4).

**Stop and resume**:

- The user can **interrupt** the analysis in progress.
- The analysis can **resume** if the user requests it.
- Once the analysis has started, it is impossible to go back to file selection (workflow).
- The system is considered **dirty** as soon as a file has been analyzed → a reset is required for a new cycle (see NFR-4).

**Progression**: Number of files analyzed / total size of the queue.

---

### F4 — Copy of clean files to the target

**Objective**: Copy the clean files to the target media.

**Optional nature**:

- The copy is **optional**: the user can stop after the analysis without copying.
- If the user wants to copy, they must plug in a target media (the source media stays plugged in).

**Trigger**:

- The copy starts **automatically** as soon as the target is available **and** the analysis is finished.
- If the target is not plugged in at the end of the analysis, the system asks the user to plug one in. The user can also choose not to plug one in (end of cycle without copy).

**Behavior**:

- Only files with `Clean` status are copied.
- The copy order is the queue order.
- The GUI displays the copy progress (files copied / total) and any failures.

**Error handling**:

- **Individual failure** (I/O, insufficient space): the copy continues on the other files. The error is reported in the GUI and in the final report.
- **Final check**: at the end, the number of copied files must be **strictly equal** to the number of clean files. Otherwise an error is triggered.

**Source media disconnection during the copy**:

- If the user unplugs the source media during the copy, it **interrupts**.
- The GUI displays an **error** prompting the user to re-insert the media to resume the copy.
- The copy **resumes automatically** as soon as the user re-inserts the source media, after a **matching verification** (notably by the disk name).

**Cancellation**:

- The user can **cancel** the copy in progress.
- A cancelled copy **cannot be resumed** (a reset will be required).

**Backlog**:

- `[feature]` Check the available space on the target before starting the copy.
- `[bug]` If the user unplugs one of the media during the workflow, the system enters an uncertain state. Disconnection handling must be reviewed.

---

### F5 — Event journal

**Objective**: Automatically record the system event journal (Safecor logs) for bug analysis or forensics.

**Behavior**:

- The system automatically records Safecor events into a journal file located in the **temporary directory**.
- The journal is **mandatory** copied onto the target media at the end of the clean files copy.
- The user **can view** the event journal from the GUI (via the `LogDialog`), read-only, during the workflow.

**Format**:

- **Native** Safecor format, without transformation.
- Each entry contains the entire information provided in the Safecor event:
  - Date and time
  - File fingerprint
  - Module (component) name
  - All other fields of the event

**Lifecycle**:

- The system is **stateless** (based on Safecor): no journal, no data is kept between cycles.
- The journal only covers the current cycle.
- After reset, the previous journal is lost.

---

### F6 — Safety report generation

**Objective**: Automatically generate a PDF safety report and copy it onto the target media.

**Trigger**:

- Automatic, at the **end of the copy** of the clean files.
- The report is generated **only if a copy took place** (no report without copy).

**Report content**:

- **System**: information provided by Safecor (version, UUID, etc.)
- **Saphir version**
- **Antivirus**: information provided by the antivirus components (name, version, description)
- **Source media**: name of the media and of the partitions
- **Analysis**:
  - Start date and time
  - End date and time
  - Total number of files analyzed
  - Total size analyzed
- **Complete list of files** (including those not copied):
  - File (path)
  - Fingerprint
  - Result of **each** antivirus
  - Retained safety result (consensus: clean / not clean)

**Format**: PDF (Jinja2 + WeasyPrint).

**Copy**:

- The report is **automatically** copied onto the target media after its generation.

**Error handling**:

- If the PDF generation fails, the user is **warned** and the cycle ends **normally** (`SystemMustBeReset` state).

---

### F7 — GUI themes

**Objective**: Offer the user the choice between several visual themes.

**Available themes**:

| Theme | Description |
|-------|-------------|
| **Light** | Default theme |
| **Dark** | For low ambient light |
| **Low visibility** | Reduces the light emitted by the system so it is less visible in a hostile environment |

**Behavior**:

- The default theme is **light** at startup.
- The user can **change theme at any time**, including during the analysis or the copy.
- **No persistence**: the choice is lost after a cycle (stateless system based on Safecor).

**Wireframe theme**:

- Reserved for **design/development** (not accessible in production).

---

### F8 — Status bar (TopBar)

**Objective**: Always display the essential system information at the top of the screen.

**Position**: Top of the screen, horizontal menu-like bar.

**Displayed elements**:

| Element | Description |
|---------|-------------|
| **Clock** | Real time (HH:MM:SS), **no date**. Simple toggle between **local** and **Zulu (UTC)** at the user's request. |
| **Battery** | Charge level (if a battery is present). |
| **Charger** | Presence of a connected charger (if applicable). |
| **Classification** | Classification level of the system, provided by **Safecor**. Tied to the hardware, **immutable** during the cycle. Displayed as a **colored label**. |

**Classification levels**:

- Unprotected
- Restricted distribution
- Secret

**Behavior**:

- The clock is updated in **real time** (every second).
- The timezone switch is a simple **toggle** (local ↔ Zulu).
- The classification is **read-only** (provided by Safecor, not modifiable by the user).

---

### F9 — System state dialog

**Objective**: Allow the user to view the state of the components and the system information.

**Access**: Dialog accessible **at any time** during the workflow.

**Content**:

**Component list**:

- Internal Safecor components (disk controller, main controller, etc.)
- Saphir antivirus components
- For each component: **name** + **state**

**Possible states of a component**:

| State | Description |
|------|-------------|
| `UNKNOWN` | Unknown state |
| `STARTING` | Starting in progress |
| `READY` | Ready |
| `ERROR` | In error |
| `OFF` | Off |

**System information**:

- Safecor version
- DEBUG mode (state provided by Safecor, enabled by the administrator/maintainer)
- Other information provided by Safecor (UUID, etc.)

**Read-only**: The dialog is purely **informational**, no action is possible from this dialog.

---

### F10 — System cleaning (reset)

**Objective**: Allow the user to clean the system to perform a new analysis on another media.

**Nature**:

- Cleaning is a **Safecor feature** (not a Saphir one).
- It destroys the disposable components: `sys-usb` virtual machine and the antivirus virtual machines.
- Saphir **completes** this feature by handling the restart of the antivirus components and the restoration of the GUI state.
- This is **not** a machine reboot or reset.

**Trigger**:

- The user can request cleaning **at any time**.
- If an **analysis** or a **copy** is in progress, the processes are **interrupted** before cleaning and the system enters a stable state.
- Once started, cleaning **cannot be cancelled**.

**Behavior during cleaning**:

- The media can **stay physically plugged in**.
- The Safecor `disk_controller` component is **disconnected** → a media disconnection message is sent.
- The `disk_controller` will automatically send a **reconnection** message of the media, identical to the first startup.
- Restarting components send state messages (`ComponentState`) as they start.
- The **cleaning progression** is displayed under the same conditions as during startup (F11).

**At the end**:

- The system has returned to its **initial state**.
- It can be used for a **new analysis**.

---

### F11 — Startup and cleaning progression

**Objective**: Display the progression of the initial startup and of the cleaning (reset) in a modal dialog.

**Trigger**:

- The dialog is tied to the **system state**: it is displayed as long as the system has not reached the `SystemReady` state.
- Used for **both** events: initial startup and cleaning/reset.

**Content**:

| Step | Dependency |
|-------|------------|
| 1. Core startup (Safecor components) | Safecor component states (`ComponentState`) |
| 2. Antivirus startup | AV component states + number started / `ANTIVIRUS_NEEDED` |
| 3. System ready | All steps 1 and 2 completed |

- **Progress bar**: reflects the overall progress.
- **Steps with states**: visual (non-textual) indicators for each step.

**Behavior**:

- **Modal**: the user cannot interact with the rest of the GUI.
- **Not closable** by the user: it is closed **automatically** when the system reaches `SystemReady`.
- The progression is updated in real time on each component state change.

---

### F12 — System shutdown

**Objective**: Allow the user to shut down the system.

**Trigger**:

- The user can request shutdown **at any time**.
- A **confirmation dialog** is displayed before shutdown.

**Behavior**:

- If work (analysis, copy) is in progress, it is **interrupted without delay**.
- **All in-progress data is lost**: no report, no copied journal.
- Shutdown triggers a call to the **Safecor API `shutdown` function**.

---

### F13 — Prompt to plug in a media

**Objective**: Inform the user to plug in a storage media once the system is ready.

**Trigger**:

- After the **complete startup** (system in `SystemReady` state, antivirus ready).
- If **no media** is plugged in when the system is ready.
- Displayed **only once**.

**Behavior**:

- **Non-modal**: the user can ignore it and continue interacting with the GUI.
- The dialog contains a **"Close"** button.
- If the user plugs in a media, the dialog is **obsolete** (does not reappear).

---

### F14 — Language selection

**Objective**: Allow the user to change the interface language.

**Behavior**:

- The user can change language **at any time**, including during the analysis or the copy.
- The change is **immediate** (all GUI strings are translated).
- The **PDF report** follows the language in effect at the time of its generation (static template per language).

**Default value**:

- After a reset, the language reverts to the one **indicated by Safecor** as the system language.

---

### F15 — Switch to the media viewer (Viewer)

**Objective**: Allow the user to switch to the media viewer to browse files.

**Configuration**:

- The feature is **managed in configuration** and enabled by the **maintainer**.
- Currently a **compile-time constant**.

**Behavior**:

- If **enabled**: a **button** is added on the GUI. When triggered, Saphir asks Safecor to **switch the display** to the Viewer component.
- If the Viewer component is **not available** (`ComponentState` ≠ `READY`):
  - The button is **unavailable**
  - The system state dialog (F9) indicates: "Viewer component not started"
- If the Viewer is **disabled** in the configuration:
  - The button **does not appear**
  - The system state dialog (F9) indicates: "disabled by configuration"

**Constraints**:

- The Viewer can only be displayed **if no operation is in progress** on the main GUI (no analysis or copy in progress).
- The **return** to Saphir is done by the same procedure from the Viewer.

**Specifications**:

- The Viewer specifications are defined in the **Viewer sub-project** (separate from Saphir).

---

### F16 — Remaining time estimation (ETA)

**Objective**: Display to the user an estimate of the remaining time for the analysis, updated in real time.

**Behavior**:

- The estimate is computed by a **weighted exponential moving average** (EMA) based on the duration and size of the already-processed files.
- The **weight** is a function of the file size: small files have a low weight, large ones a high weight, in order to minimize the impact of duration differences between iterations.
- The ETA is displayed in the **analysis progress gauge** (F3) as `ETA: <readable duration>`.
- The readable duration is formatted in **days / hours / minutes**.
- The estimate is **reset** at each analysis start with the total size of the queue.

**Dependencies**: F3 (antivirus analysis).

**Backlog**:

- `[fix]` The displayed duration units (`j`/`h`/`min`) use untranslated French abbreviations — to be fixed to comply with NFR-5.

---

### F17 — Analysis list filters

**Objective**: Allow the user to filter the display of the list of analyzed files by status.

**Behavior**:

- The analysis list (F3) exposes three toggleable **filters**: **Clean**, **Infected**, **Waiting**.
- Each filter is **active by default**.
- The filter applies to the **display** of the list **without** modifying the underlying data.
- The filter applies according to the file status (clean / infected / waiting for processing).

**Dependencies**: F3 (antivirus analysis).

**Backlog**:

- `[fix]` The third filter label ("Waiting" in PC layout, "Other" in tablet layout) is inconsistent — to be harmonized.

---

### F18 — System messages `[deprecated]`

**Status**: **Deprecated** — the code is kept during the refactoring, the decision to remove or reactivate it will be made later.

**Objective**: Display to the user a feed of information messages about the system progress.

**Behavior**:

- The system emits information messages (e.g.: "Saphir has started…", "The antivirus engines are ready", "The system is cleaning…", "The report and the journal have been copied").
- The messages are displayed in a message panel (chronological feed) on the GUI.
- The messages are translated (NFR-5) at the source level.
- The messages are ephemeral: cleared on a reset (stateless system).

**Current state**: the message panel is **hidden** (`visible: false`) — the feature is inert.

**Pending decision**: reactivate the feature or remove the code (panel + model + message emission).

---

### F19 — Ambient light indicator `[not ready]`

**Status**: **Not ready** — the feature is planned but **Safecor does not provide yet** the light information. The code is kept, the feature will be enabled when Safecor exposes the data.

**Objective**: Display in the status bar (F8) an indicator of the ambient light intensity detected by a sensor.

**Behavior**:

- A glyph is displayed in the status bar according to the light level (low / medium / high).
- The display depends on the availability of a **light sensor** (`ambientLightSensorReady`) and the measured value (`ambientLight`, 0-100).

**Blocker**: no light data is provided by Safecor to date — `ambientLightSensorReady` and `ambientLight` are hardcoded.

**Backlog**:

- `[fix]` The font used (`Material Symbols Outlined`) is not installed by `main.py` — to be fixed before enabling.
- `[dependency]` Enable the feature when Safecor exposes the light sensor state.

---

### F20 — Fullscreen execution mode & cursor handling

**Objective**: The system runs in **fullscreen** on a dedicated station (nominal mode) and adapts the cursor display to the input device type of the device.

**Behavior**:

- The system runs **in fullscreen** on a dedicated system — this is the **nominal mode**.
- The device can be **touch** or equipped with a **mouse and keyboard**.
- **Fullscreen** can only be disabled in **DevMode**.
- When the device runs in **touch mode**, the **mouse cursor is hidden**.
- On a device equipped with a mouse, the cursor reappears upon movement.

**Dependencies**: F8 (TopBar), global navigation.

**Note**: this feature may be handled by Safecor; it is kept here for the moment.

---

### F21 — Adaptive layout according to device type `[backlog]`

**Status**: **To be done** — the feature is planned but **not implemented** (the PC layout is currently inert). Kept in the backlog.

**Objective**: Adapt the GUI layout to the target device type (touch "handheld" terminal vs "PC" workstation).

**Behavior**:

- The `handheld` property determines the **layout**: row heights, filter style (F17), panel templates.
- The **handheld** mode corresponds to the touch terminals of the station.
- The **PC** mode corresponds to workstations equipped with a keyboard and a mouse.

**Current state**: `handheld` is **always `True`** (backend constant + hardcoded in `Bindings.qml`) → the **PC layout is inert** (never displayed).

**To do**:

- Make `handheld` a property genuinely **configured according to the device**.
- Rehabilitate or remove the PC layout.

---

## 2. Non-functional requirements (NFR)

### NFR-1 — End-to-end integrity verification (fingerprint)

**Principle**: Every operation on a file (read, copy, antivirus analysis) must be preceded and followed by a verification of its fingerprint. Objective: guarantee the absence of file alteration end-to-end — the file copied onto the target must be identical to the source file.

**Roles**:

- **Safecor** automatically computes the fingerprint on each operation on a file. The algorithm is Safecor's (irrelevant for Saphir). All fingerprints are comparable end-to-end.
- **Saphir** must ensure non-alteration by comparing the fingerprints at each step.

**Verification points**:

| Step | Verification |
|-------|-------------|
| Source copy → local repository | Saphir obtains a first fingerprint. The match with the original is **guaranteed by Safecor**. This fingerprint is associated with the file in the queue data structure. |
| Antivirus analysis | The Saphir AV components must **verify** that the fingerprint of the file in the repository matches the recorded one. |
| Repository copy → target | Safecor computes the fingerprint of the copied file. Saphir must **verify** that this fingerprint matches that of the original file. |

**Verification failure**:

- The file is declared **`Error`** (not clean, not copyable).
- The processing chain **continues** on the other files.
- The error is traced in the journal and the report.

---

### NFR-2 — Source media integrity

**Principle**: The source media must not be altered.

**Roles**:

- **Saphir**: by design, must **never** attempt to create or modify files on the source media. Read-only.
- **Safecor**: does **not** block writes on the source (no read-only mounting). The responsibility lies with Saphir.

**Verification**:

- The current mechanism (fingerprint on read, see NFR-1) is **sufficient** for the moment.

---

### NFR-3 — Minimum number of required antivirus engines

**Principle**: The system is configured by the maintainer to be usable only if a certain number of antivirus engines is available for the analysis. Saphir **must not be able to operate** (start the analysis) if this number is not reached.

**Configuration**:

- The value is a **compile-time constant**, hard-coded in the configuration.
- It must be **consistent with the product packaging** (number of antivirus components integrated into the product).
- Currently: `ANTIVIRUS_NEEDED = 2`.

**Behavior if unavailable**:

- The startup/cleaning progression dialog stays **pending** until all required antivirus engines are available.
- The user **can select** files (navigation, enqueue).
- The **analysis start button is disabled** as long as the minimum number is not reached.

**Failure during analysis**:

- If an antivirus engine fails **during** the analysis:
  - If the failure is **detected**, the analysis result for this engine switches to **error**.
  - The concerned files will therefore have an `Error` (not clean) status instead of a valid consensus.
  - Files already analyzed **keep** their status.

---

### NFR-4 — Dirty state and locking

**Principle**: As soon as a file has been read by the system, it becomes **dirty**. At the end of the operation, the user has no other choice than to **clean** (reset) or **shut down** the system.

**Contamination point**:

- The system becomes dirty as soon as the **`disk-controller`** component of Safecor has **effectively read** the file.
- Simple navigation in the tree does not contaminate.

**Locking by media change**:

- If the user **disconnects** the media and **connects another one** (**different** disk names), the system **locks**:
  - State: `SystemMustBeReset`
  - A **dialog** is displayed
  - No action possible except **clean** or **shut down**
- If the user disconnects and **reconnects the same media** (same disk name), they **can continue**.

---

### NFR-5 — Translatability

**Principle**: All character strings displayed on the screen **and** written in the report must be translatable.

**Languages**:

- Currently: **EN** and **FR**.
- Other languages will be added later.

**Mechanisms**:

- **GUI**: **Qt** mechanisms only (`tr()`, `.ts`/`.qm` files).
- **PDF report**: **static** translation — a **template file per language** (dedicated Jinja2 template for each language).

---

## 3. Consolidated backlog

| Type | Reference | Description |
|------|-----------|-------------|
| `[bug]` | F1 | "Scan all" mode: verify that all partitions are properly analyzed |
| `[feature]` | F1 | Allow the user to undo their mode choice without a reset |
| `[feature]` | F2 | Mechanism for a full queue drain (clear queue) |
| `[feature]` | F4 | Check the available space on the target before starting the copy |
| `[bug]` | F4 | Media disconnection during the workflow → uncertain state |
