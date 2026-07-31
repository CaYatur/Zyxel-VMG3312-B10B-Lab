# CaYaRouter Lab — Zyxel VMG3312-B10B

> **Experimental:** This repository documents research and customization work on an existing Zyxel VMG3312-B10B. It is not a finished router product, an original modem design, or production-ready firmware.

CaYaRouter Lab is a device-specific workspace for examining and improving the management interface and firmware structure of the **Zyxel VMG3312-B10B**.

The goal is to preserve the modem's stock Broadcom hardware layer while researching a safer, modern management interface and carefully scoped feature additions.

## Current capabilities

- Read-only modem inventory and endpoint mapping
- Authenticated menu, page, and feature discovery
- Local HTTP proxy for reaching the Zyxel over LAN while Wi-Fi remains connected to another router using the same subnet
- Windows DPAPI-backed local credential storage
- Configuration backup tooling with SHA-256 verification
- Firmware and web-interface structure research
- Safety filters that block reboot, reset, restore, upload, firmware, delete, apply, and other state-changing endpoints during inventory scans

## Target architecture

```text
CaYaRouter UI
    -> lightweight CaYa API
    -> existing Zyxel user-space services
    -> stock Broadcom kernel and hardware drivers
```

The project does **not** currently replace the bootloader, Linux kernel, DSL driver, Wi-Fi driver, Ethernet switch driver, or hardware NAT layer.

## Repository layout

```text
tools/
  windows_dpapi_store.py       Local Windows-user-bound credential vault
  zyxel_local_proxy.py         Local proxy to the modem through a selected LAN IP
  zyxel_readonly_inventory.py  Read-only page and endpoint inventory
  zyxel_endpoint_mapper.py     JavaScript and dynamic endpoint mapper
  zyxel_tab_mapper.py          Zyxel menu/tab tree mapper
  zyxel_backup_config.py       Configuration backup downloader and verifier
  firmware_inspect.py          Offline firmware signature, region, and JFFS2 validator
  jffs2_path_mapper.py         Big-endian JFFS2 inode and path mapper
  jffs2_extract.py             CRC-verified JFFS2 regular-file extractor
  stock_ui_preview.py          Read-only local preview server for the extracted stock UI
  prepare_custom_firmware_workspace.py  Adds /caya/ without replacing stock UI
  firmware_candidate_guard.py  Conservative offline custom-image checks
  build_caya_firmware_linux.sh Vendor-tool fs+kernel build recipe for Linux

docs/
  firmware-analysis.md         Public summary of the stock AAPP7 image analysis
  custom-firmware-build.md     Custom build scope, validation, and recovery status

ui-prototype/
  index.html                   Full CaYaRouter Lab management shell
  full-styles.css              Responsive light/dark management interface
  full-app.js                  Complete feature catalog and local demo data layer
  styles.css                   Earlier dashboard prototype styles
  app.js                       Earlier dashboard prototype interactions
```

Generated modem reports, authenticated captures, credentials, configuration backups, raw firmware images, and other sensitive device data are intentionally excluded from Git.

## Safety model

The research tools follow these rules:

- Only the login action uses POST.
- Inventory and mapping requests use GET only.
- Known state-changing paths are blocked.
- Credentials are not written to source files or reports.
- Local credentials are protected with Windows DPAPI.
- Configuration backups are stored under `.caya-agent/` and ignored by Git.
- No firmware flashing, reboot, reset, restore, or configuration-changing operation is performed by the inventory tools.

## Status

Completed:

- Device access over isolated LAN4 connection
- Authenticated UI mapping
- Main menu and tab discovery
- Feature inventory
- Local encrypted credential storage
- Configuration backup
- Offline stock firmware identity and region analysis
- Big-endian JFFS2 validation and complete path reconstruction
- CRC-verified root filesystem extraction
- Read-only local preview of the extracted stock web interface
- Responsive CaYaRouter Lab dashboard prototype with light/dark themes
- Full management UI coverage for WAN/DSL, LAN/DHCP, Wi-Fi, NAT, QoS, security, parental control, IPSec, USB, monitoring, logs, diagnostics, and maintenance
- Browser-local demo persistence for forms, switches, tables, add/edit/delete flows, filtering, and diagnostics

Planned:

- Vendor firmware header and checksum field analysis
- Read-only live-data adapter for the CaYaRouter dashboard
- Lightweight API adapter for stock Zyxel services
- Recovery workflow documentation
- Controlled test build that changes only non-critical web assets

## Disclaimer

This project may permanently damage unsupported hardware if experimental firmware is written incorrectly. Do not flash modified images without a verified recovery path, full flash backup, and an understanding of the device-specific bootloader and partition layout.
