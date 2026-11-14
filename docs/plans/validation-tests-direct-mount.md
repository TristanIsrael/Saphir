# Validation tests

Scope: Direct mount Safecor features added into Saphir. The problems belong to both Saphir and Safecor.

## Run 1

- [FIXED] The storage setting of the XL files should be removed from saphir-gui, saphir-viewer, saphir-av-clamav, saphir-av-eset and sys-usb.
- [FIXED] The domain `sys-usb` should be declared `driver_domain` (`driver_domain = 1` in `sys-usb.conf`).
- [FIXED] PCI passhtrough is not available in PVH Domains. The domain sys-usb should be in `pv` mode instead of `pvh`.
- When the Dom0 starts it keeps spamming the message bus with the following messages and it does not answer to the message `system/topology/my_config` for example:
  - `{"component": "saphir", "module": "System controller", "datetime": "2026-11-14 22:24:35.007", "description": "Safecor Dom0 controller is ready"}`
  - `{"component": "saphir", "module": "System controller", "datetime": "2026-11-14 22:24:36.051", "description": "Default language defined on the kernel's command line is en"}`
  - `{"component": "saphir", "module": "System controller", "datetime": "2026-11-14 22:24:35.007", "description": "Safecor Dom0 controller is ready"}`
  - `{"component": "saphir", "module": "System controller", "datetime": "2026-11-14 22:24:36.051", "description": "Default language defined on the kernel's command line is en"}`
- The command `my_config` should send the Domain's configuration only and it seems to be sending the whole topology.json.

## Packages repository redesign

We want to completely get rid of the `9p` sharing.

  - Now during the installation, we download the `apk` files in `/usr/lib/safecor/packages`
  - Instead we should create a squashfs containing all the packages. The command is `$ mksquashfs packages packages.squashfs -comp zstd -Xcompression-level 1 -b 128K -noappend -no-xattrs`
  - The squashfs should be created by the github CI and published on the server. 
  - The squashfs will be packed in the ISO image of Saphir.
  - The squashfs should not be loaded in memory when the system boots in diskless mode (USB key) and mounted directly from the USB disk.

## Future improvements

This section contains entries for the backlog.

- The action build-and-publish-iso is broken with Alpine 3.24. Needs to fixed later.
