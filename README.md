# CaYaRouter

> **Experimental:** This project is under active research and is not ready for production use or firmware flashing.

CaYaRouter is an experimental management, reverse-engineering, and firmware-research project for the **Zyxel VMG3312-B10B** router/modem.

The long-term goal is to build a modern CaYaRouter management layer while preserving the stock Broadcom kernel, DSL, Wi-Fi, Ethernet, and hardware-acceleration components that are difficult to replace safely.

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

Planned:

- Firmware header and checksum analysis
- Stock web-interface extraction and comparison
- Read-only CaYaRouter dashboard prototype
- Lightweight API adapter for stock Zyxel services
- Recovery workflow documentation
- Controlled test build that changes only non-critical web assets

## Disclaimer

This project may permanently damage unsupported hardware if experimental firmware is written incorrectly. Do not flash modified images without a verified recovery path, full flash backup, and an understanding of the device-specific bootloader and partition layout.
