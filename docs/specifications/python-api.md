# Saphir — Safecor Python API Reference

> **Status**: Stable
> **Last updated**: 2026-11-20
> **Audience**: developers (human and AI agents) writing Saphir code that talks to the Safecor platform
> **Scope**: an **offline reference copy** of the Safecor Python API **as used by Saphir** — what Saphir imports, the `Api` singleton lifecycle and high-level calls, the full `Topics` constant list, the request/response semantics, and the supporting helpers. This is not an exhaustive dump of every Safecor method — see the Safecor repo for the rest.

> **Offline reference copy** — Source: Safecor repo `python/lib/src/safecor/`. Synced: 2026-11-20. When Safecor changes, update here and log the divergence in `docs/safecor-divergences.md`.

## Related documents

| Concern | Document |
|---------|----------|
| MQTT topic payloads & Saphir custom topics | [`../development/protocol.md`](../development/protocol.md) |
| Single-client constraint & API ownership (invariants I1/I2) | [`../architecture/decisions/0002-per-domain-single-api-client.md`](../architecture/decisions/0002-per-domain-single-api-client.md) |
| Repository as the only data exchange point | [`../architecture/decisions/0003-repository-only-data-exchange.md`](../architecture/decisions/0003-repository-only-data-exchange.md) |
| Event-driven design (no polling) | [`../architecture/decisions/0001-event-driven-no-polling.md`](../architecture/decisions/0001-event-driven-no-polling.md) |
| Divergences noticed in Safecor | [`../safecor-divergences.md`](../safecor-divergences.md) |
| Upstream sources of truth (Safecor repo & wiki) | [`../safecor-refs.md`](../safecor-refs.md) |

The library is the `safecor` Python package (Safecor repo `python/lib/src/safecor/`). All symbols below are exported at the package root (`from safecor import ...`).

---

## 1. What Saphir imports

| Symbol | Kind | Used by Saphir for |
|--------|------|--------------------|
| `Api` | class (singleton) | The high-level API entry point: connect, subscribe, publish, platform requests, logging |
| `Topics` | class of constants | The MQTT topic names (see §4) |
| `MqttFactory` | class (static) | Creating the DomU / Dom0 / debug MQTT clients |
| `MqttClient` | class | Low-level client (created directly in DEVMODE) |
| `ConnectionType` | enum | `UNIX_SOCKET` (production) vs `TCP_DEBUG` (DEVMODE) |
| `MqttHelper` | class (static) | `check_payload(payload, keys)` — validate a received payload has the expected keys |
| `ComponentsHelper` | class | Track the component list/states from `discover_components` responses (F9, AV readiness) |
| `ComponentState` | enum | Component states: `unknown`, `starting`, `ready`, `error`, `off` |
| `DiskState` | enum | Disk states: `unknown`, `connected`, `disconnected`, `mounted`, `unmounted` |
| `FileHelper` | class (static) | `calculate_fingerprint(path)` (md5), `is_archive_file(name)` |
| `Logger` | class (singleton) | Low-level MQTT logger (Saphir mostly logs through `Api().info/error/...`) |
| `System` | class (singleton) | Platform info: `get_system_information()`, `domain_name()`, screen size/rotation, `is_usb_mountpoint_ready()` (v2), `on_usb_mountpoint_ready(callback)` (v2) |
| `Constants` | class of constants | Platform constants: `STR_REPOSITORY` (deprecated), `DOMU_REPOSITORY_PATH` (deprecated), `FINGERPRINT_METHOD`, ... |
| `NotificationFactory` | class (static) | Craft notification payloads (used by mocks & tests) |
| `ResponseFactory` | class (static) | Craft response payloads (used by mocks & tests) |
| `__version__` | str | The Safecor version (set as the application version by `main.py`) |
| `MountMode` | enum | v2: `MountMode.RO`, `MountMode.RW` (used by `DirectMountManager`) |
| `DirectMountManager` | class (v2) | v2: manages the `/media/usb` direct mount lifecycle |

> `MockSysUsbController`, `MockDom0Controller`, `Emulator`, `default_profile` are **not** part of the `safecor` package — they come from the **`safecor_emulator`** package (Safecor repo `python/emulator/`). See [`../development/testing.md`](../development/testing.md) §3.2.

---

## 2. The `Api` singleton

`Api` is a **singleton** (`SingletonMeta`): one instance per process. Since each Safecor domain is its own VM/process, the constraint is **per-domain** — the GUI, ClamAV and ESET domains each hold their own `Api()`. Only one object per process may own the client; in Saphir the GUI centralises it in `ApiLifecycle` (invariant I1, see [`../architecture/decisions/0002-per-domain-single-api-client.md`](../architecture/decisions/0002-per-domain-single-api-client.md)).

### 2.1 Lifecycle — start, ready, subscribe, subscribed

```python
from safecor import Api, MqttFactory

# 1. Create the client:
#    production : MqttFactory.create_mqtt_client_domu("GUI")  (UNIX vchan socket)
#    DEVMODE    : MqttClient("GUI", ConnectionType.TCP_DEBUG, "localhost")
client = MqttFactory.create_mqtt_client_domu("GUI")

# 2. Start the API (connects to the broker, opens the log file if recording)
Api().add_ready_callback(on_ready)            # no argument
Api().start(mqtt_client=client,
            domain_identifier="GUI",
            recording=True,
            logfile="/tmp/saphir.log")

# 3. In on_ready(): subscribe (the broker must acknowledge each subscription)
ok, mid = Api().subscribe(Topics.DISK_STATE)  # (True, mid) or (False, None); None if already subscribed
Api().add_subscription_callback(on_subscribed)  # (mid) — broker acknowledged
Api().add_message_callback(on_message)          # (topic, payload)

# 4. In on_subscribed(mid): continue the app once every subscription is confirmed
```

The mandatory sequence is **start → on ready → subscribe → on subscribed → continue** (the app must not send requests before the broker confirms the subscriptions). On Saphir, `ApiLifecycle.setup_subscriptions()` subscribes to all the required topics and fires an "all-ready" callback once every `mid` has been acknowledged.

On connect, `Api` **automatically subscribes** to `{Topics.PING}/{domain}/request`, `{Topics.SHUTDOWN}/response` and `{Topics.RESTART_DOMAIN}/response` (these responses are intercepted internally and dispatched to the shutdown/restart callbacks).

### 2.2 Callbacks

| Callback | Arguments | Fired when |
|----------|-----------|------------|
| `add_ready_callback(fn)` | — | the client is connected to the broker |
| `add_message_callback(fn)` | `(topic: str, payload: dict)` | a message arrives on a subscribed topic |
| `add_subscription_callback(fn)` | `(mid: int)` | the broker acknowledged a subscription |
| `add_shutdown_callback(fn)` | `(success: bool, reason: str)` | the `shutdown` response is accepted/refused |
| `add_restart_callback(fn)` | `(domain_name: str, success: bool, reason: str)` | the `restart_domain` response is accepted/refused |

All handlers run **on the MQTT thread**: they must be thread-safe and must not block.

### 2.3 Basic operations

| Call | Purpose |
|------|---------|
| `Api().stop()` | Disconnect from the broker |
| `Api().get_mqtt_client()` | The underlying `MqttClient` |
| `Api().subscribe(topic)` → `(bool, mid \| None)` | Subscribe (idempotent: `None` if already subscribed) |
| `Api().publish(topic, payload: dict)` | Publish a JSON payload on an arbitrary topic (Saphir uses it for the custom `saphir/analysis/*` topics and for raw `{Topics.X}/request` payloads) |
| `Api().debug/info/warn/error/critical(message, module="")` | Publish a log event on `system/events/{level}` (module defaults to the domain name; Saphir passes `"Saphir"`) |

### 2.4 High-level platform calls (as used by Saphir)

Each call publishes `{topic}/request`; the answer arrives later on `{topic}/response` (or as a notification), delivered to the registered message callback. Payload shapes are in [`../development/protocol.md`](../development/protocol.md).

| Call | Request topic | Response / notification |
|------|---------------|--------------------------|
| `get_disks_list()` | `system/disks/list_disks` | `{topic}/response` — list of disks |
| `get_files_list(disk, recursive=False, from_dir="", name_filters=None)` | `system/disks/list_files` | `{topic}/response` — file/folder entries |
| `read_file(disk, filepath)` | `system/disks/read_file` | **deprecated** — no longer used (direct mount, see [ADR 0019](../architecture/decisions/0019-direct-usb-mount-data-path.md)) — `system/disks/new_file` notification |
| `get_file_fingerprint(disk, filepath)` | `system/disks/file_fingerprint` | fingerprint of a file on the source media (analysis precondition) |
| `copy_file(source_disk, filepath, destination_disk)` | `system/disks/copy_file` | `{topic}/response` — status + destination fingerprint |
| `create_file(filepath, disk, contents, binary=False)` | `system/disks/create_file` | `{topic}/response` (`success` gates the workflow); binary content is base64 (+zlib when `binary`) |
| `delete_file(filepath, disk)` | `system/disks/delete_file` | **deprecated** — no longer used (no repository staging) — `system/disks/deleted_file` notification |
| `request_repository_path()` | `system/disks/repository_path` | **deprecated** — no longer used (mount readiness via `System.is_usb_mountpoint_ready()`) |
| `discover_components()` | `system/discover/components` | `{topic}/response` — the component list |
| `publish_components(components: list)` | — | Saphir **publishes** on `{topic}/response` to answer a discovery request (AV domains advertise `type: "antivirus"`) |
| `request_energy_state()` | `system/energy/state` | `{topic}/response` — battery level + plugged (the only polling in the system: 5 s timer) |
| `request_system_info()` | `system/info` | `{topic}/response` — core/system/storage info (F9, repository capacity) |
| `clear_sys_usb_queues()` | `system/sys-usb/clear-queues` | `{topic}/response` — cancels in-flight repository reads (Pause) |
| `get_default_language()` | `system/settings/languages/default` | `{topic}/response` — ISO2 language |
| `notify_gui_ready()` | — | notification `system/workflow/gui_ready` `{}` — **mandatory**: removes the splash screen |
| `shutdown()` | `system/workflow/shutdown` | response via `add_shutdown_callback` |
| `restart_domain(domain_name)` | `system/workflow/restart_domain` | response via `add_restart_callback`; AV domains also **subscribe** to this topic to restart themselves when addressed |
| `switch_gui(domain_name)` | `system/gui/switch` | `{topic}/response` — swap the visible GUI domain (Saphir ↔ Viewer) |
| `mount_file(disk, filepath)` / `unmount(disk)` | `system/disks/mount_file` / `unmount` | disk-state notification — archive mounting; the Saphir code path is gated by the `MOUNT_ARCHIVES` constant (dormant, see [`../architecture/decisions/0018-archive-mounting-removed.md`](../architecture/decisions/0018-archive-mounting-removed.md)) |

Also available (not used by Saphir today): `get_languages_list()`, `get_current_language()`, `set_current_language()`, `ping()`, `archive_extensions_handled()`.

> **Safecor v2 additions (used in Saphir v4)**: `System.is_usb_mountpoint_ready()` (bool), `System.on_usb_mountpoint_ready(callback)` (register callback for mount readiness), `MountMode` enum, `DirectMountManager`.

---

## 3. Request/response semantics

- The API is **asynchronous**: a high-level call publishes a `/request`; the result arrives later on the matching `/response` topic (or as an unsolicited notification) and is dispatched to the registered message callback. There is no return value carrying the result.
- **Notifications** (no `/request`) arrive as unsolicited messages: `system/disks/state`, `system/disks/new_file`, `system/disks/deleted_file`, `system/workflow/gui_ready`, `system/events/*`.
- Responses are delivered only when (a) the topic is subscribed and (b) a message callback is registered.
- `read_file` and `delete_file` have **no direct response**: completion is signalled by the `new_file` / `deleted_file` notifications (the platform computes the fingerprints on the way — NFR-1).
- Saphir validates every received payload with `MqttHelper.check_payload(payload, [required_keys])` before processing it.

---

## 4. `Topics` constants

Full list of the `Topics` class constants (values are exact strings):

| Constant | Value | Constant | Value |
|----------|-------|----------|-------|
| `SYSTEM` | `system` | `DISCOVER_COMPONENTS` | `system/discover/components` |
| `DISKS` | `system/disks` | `KEEPALIVE` | `system/misc/ping` |
| `MISC` | `system/misc` | `ENERGY_STATE` | `system/energy/state` |
| `EVENTS` | `system/events` | `SYSTEM_INFO` | `system/info` |
| `DISCOVER` | `system/discover` | `BENCHMARK` | `system/misc/benchmark` |
| `WORKFLOW` | `system/workflow` | `SYS_USB_CLEAR_QUEUES` | `system/sys-usb/clear-queues` |
| `ENERGY` | `system/energy` | `ERROR` | `system/events/error` |
| `SYS_USB` | `system/sys-usb` | `WARNING` | `system/events/warning` |
| `SETTINGS` | `system/settings` | `INFO` | `system/events/info` |
| `GUI` | `system/gui` | `DEBUG` | `system/events/debug` |
| `TOPOLOGY` | `system/topology` | `SET_LOG_LEVEL` | `system/events/set_loglevel` |
| `DEBUGGING` | `system/debugging` | `SAVE_LOG` | `system/events/save_log` |
| `LIST_DISKS` | `system/disks/list_disks` | `PING` | `system/debugging/ping` |
| `LIST_FILES` | `system/disks/list_files` | `SETTING_CHANGED` | `system/settings/changed` |
| `READ_FILE` | `system/disks/read_file` | `LANGUAGES` | `system/settings/languages` |
| `COPY_FILE` | `system/disks/copy_file` | `LIST_LANGUAGES` | `system/settings/languages/list` |
| `DELETE_FILE` | `system/disks/delete_file` | `DEFAULT_LANGUAGE` | `system/settings/languages/default` |
| `FILE_FINGERPRINT` | `system/disks/file_fingerprint` | `CURRENT_LANGUAGE` | `system/settings/languages/current` |
| `CREATE_FILE` | `system/disks/create_file` | `SET_LANGUAGE` | `system/settings/languages/set` |
| `NEW_FILE` | `system/disks/new_file` | `SWITCH_GUI` | `system/gui/switch` |
| `DISK_STATE` | `system/disks/state` | `MY_CONFIG` | `system/topology/my_config` |
| `MOUNT_FILE` | `system/disks/mount_file` | `SHUTDOWN` | `system/workflow/shutdown` |
| `UNMOUNT` | `system/disks/unmount` | `RESTART_DOMAIN` | `system/workflow/restart_domain` |
| `DELETED_FILE` | `system/disks/deleted_file` | `GUI_READY` | `system/workflow/gui_ready` |
| `REPOSITORY_PATH` | `system/disks/repository_path` | | |

Request/response functions are the `<topic>/request` + `<topic>/response` pair; notifications are single topics with no `/request`. The Saphir custom topics (`saphir/analysis/*`) are **not** part of this class — they are defined by Saphir in `libsaphir` (`TOPIC_ANALYSIS = "saphir/analysis"`, see [`../development/protocol.md`](../development/protocol.md)).

---

## 5. Supporting helpers

### 5.1 `MqttFactory` (static)

| Method | Client created |
|--------|----------------|
| `create_mqtt_client_domu(identifier)` | `MqttClient(identifier, UNIX_SOCKET, "/var/run/safecor/mqtt.sock")` — the production DomU path (vchan) |
| `create_mqtt_client_dom0(identifier)` | `MqttClient(identifier, UNIX_SOCKET, "/tmp/mqtt-dom0.sock")` — the Dom0 path |
| `create_mqtt_network_dev(identifier)` | `MqttClient(identifier, TCP_DEBUG, "localhost")` — development broker |

`ConnectionType`: `UNIX_SOCKET = "unix_socket"`, `TCP_DEBUG = "tcp"`. Saphir's `DevModeHelper.create_mqtt_client(identifier)` builds the `TCP_DEBUG` client directly.

### 5.2 `MqttClient`

Low-level paho client. Attributes: `identifier`, `connection_type`, `connection_string`, `connected`, `is_starting`; callbacks `on_connected()`, `on_message(topic, payload)`, `on_subscribed(mid)`, `on_log(level, buf)`. Methods: `start()`, `stop()`, `subscribe(topic)`, `unsubscribe(topic)`, `unsubscribe_all()`, `publish(topic, payload)` (JSON-serialized), `add_message_callback(cb)`, `del_message_callback(cb)`, `add_connected_callback(cb)`.

### 5.3 `ComponentsHelper`

Tracks the component list from `discover_components` responses: `update(components)` (upsert by `id`, state translated to `ComponentState`), `get_state(id)` → `ComponentState`, `is_ready(id)` → `bool`, `get_by_id(id)` → dict, `get_ids()`, `get_ids_by_type(type)`, `get_states()` → `{id: state}`, `get_components()`, `get_type(id)`, `clear()`.

Saphir: the GUI uses it for the component list (F9) and the AV readiness conditions; each AV domain publishes its state with `Api().publish_components([...])` (`type: "antivirus"`, `state: ready` only when the repository path is known **and** the engine is initialised).

### 5.4 `System`

`get_system_information()` → the `system/info` payload (core version, os, cpu, memory, load, boot_time, uuid, storage); `domain_name()` → the hostname (the domain name); `get_screen_width()/get_screen_height()/get_screen_rotation()` (DomU, from xenstore); `get_system_uuid()` (from DMI); `is_usb_mountpoint_ready()` → `bool` (v2: whether `/media/usb` is mounted); `on_usb_mountpoint_ready(callback)` → register a callback fired when the USB mountpoint becomes ready (v2). Saphir uses `get_system_information()` in mocks/tests, `domain_name()` indirectly through the logging, and the screen size in `main.py`. In Saphir v4, `is_usb_mountpoint_ready()` / `on_usb_mountpoint_ready()` are used as the readiness gate for AV domains (replacing the old `request_repository_path()` pattern).

### 5.5 `FileHelper` (static)

- `calculate_fingerprint(filepath)` → md5 hex digest (`Constants.FINGERPRINT_METHOD = "md5"`); used by the AV domains for the NFR-1 repository integrity check and by tests.
- `is_archive_file(filename)` → `True` when the extension is in `Constants.ARCHIVE_EXTENSIONS_HANDLED`.
- Others (platform-side, not used by Saphir apps): `get_disks_list()`, `get_files_list()`, `copy_file()`, `create_file()`, `remove_file()`, `get_mount_point()`.

### 5.6 `Logger` (singleton)

`debug/info/warning/warn/error/critical(description, module="")` publish `system/events/{level}` payloads `{component, module, datetime, description}`; `setup(module_name, mqtt_client, recording=..., filename=...)` wires it to a client and optionally records events to a file. `Api()` sets it up automatically on connect (Saphir starts the API with `recording=True`, which produces the journal file). `Logger.print(message)` formats a stdout log line.

### 5.7 `NotificationFactory` / `ResponseFactory` (static)

Payload builders — used by Saphir **mocks and tests** to craft platform messages (the real appliance sends them): `create_notification_disk_state(disk, state)`, `create_notification_new_file(disk, filepath, source_fingerprint, dest_fingerprint)`, `create_notification_deleted_file(disk, filepath)`, `create_response_list_files(disk, files)`, `create_response_language_default(language)`, ...

### 5.8 `Constants` (values used by Saphir)

| Constant | Value | Used for |
|----------|-------|----------|
| `STR_REPOSITORY` | `__repository__` | ~~deprecated~~ — no longer used (see [ADR 0019](../architecture/decisions/0019-direct-usb-mount-data-path.md)) |
| `DOMU_REPOSITORY_PATH` | `/mnt/storage` | ~~deprecated~~ — no longer used |
| `FINGERPRINT_METHOD` | `md5` | `FileHelper.calculate_fingerprint` |
| `ARCHIVE_EXTENSIONS_HANDLED` | list (`.zip`, `.7z`, ...) | `FileHelper.is_archive_file` |
| `MQTT_VCHAN_SOCKET` | `/var/run/safecor/mqtt.sock` | The DomU broker socket |
| `LOCAL_LOG_FILEPATH` | `/var/log/safecor/safecor.log` | Default API log file |

### 5.9 `ComponentState` / `DiskState`

`ComponentState` (str enum): `UNKNOWN="unknown"`, `STARTING="starting"`, `READY="ready"`, `ERROR="error"`, `OFF="off"`.
`DiskState` (str enum): `UNKNOWN="unknown"`, `CONNECTED="connected"`, `DISCONNECTED="disconnected"`, `MOUNTED="mounted"`, `UNMOUNTED="unmounted"`.

---

## 6. How Saphir boots the API

Production (GUI domain, `ApplicationController.start()`):

```python
client = MqttFactory.create_mqtt_client_domu("GUI")
Api().add_ready_callback(self.__on_api_ready)
Api().start(mqtt_client=client, domain_identifier="GUI",
            recording=True, logfile=self.__api_lifecycle.get_logfile())
```

DEVMODE (no appliance): the client is `MqttClient("GUI", ConnectionType.TCP_DEBUG, "localhost")` — everything else is identical (the broker is the local Mosquitto of the emulator or the dev environment).

On `on_api_ready`, the GUI registers its message/subscription callbacks and runs `ApiLifecycle.setup_subscriptions()`; the application continues once every subscription is acknowledged. The AV domains follow the same pattern (one `Api()` per domain) and additionally subscribe to `system/workflow/restart_domain` to restart themselves on a reset.
