# Project Guidelines

!IMPORTANT: and new finding about flash programing or connectivity to device (serial, ethernet, etc) should be added to this file and the README.md files, and the instructions should be updated to reflect the new understanding. For example, if we find that the serial console is not working due to permissions, we should add instructions for setting up udev rules to allow access to the serial devices.

# Configuration
this device is using nvme - not mmc !
!IMPORTNAT - for flash programing do not use mmc but nvme

## Scope
- This root workspace includes documentation archives, downloaded NVIDIA bundles, and active development under `nvidia_sdk/`.
- Prefer edits in source/config/workflow files, not large binary artifacts (for example `*.tbz2`, model weights, generated run outputs).


## Architecture
- Root-level layout:
  - `doc/`: mirrored/reference documentation.
  - `nvidia_download/`: downloaded SDK metadata and archives.
  - `nvidia_sdk/`: active project area (JetPack/L4T tools, skills, scripts, and experiments).
- Treat `nvidia_sdk/JetPack_6.2.2_Linux_JETSON_ORIN_NANO_TARGETS/Linux_for_Tegra` as the main editable Jetson platform tree.

## Build And Test
- No single workspace-wide build/test command exists at the root.
- For Jetson flashing/build flows, run commands from `nvidia_sdk/JetPack_6.2.2_Linux_JETSON_ORIN_NANO_TARGETS/Linux_for_Tegra`  Before running expensive operations, prefer targeted checks and dry-run style validation where available.

## Flash Programming Notes
- Use this as a quick checklist before any flash action, with details in `doc/qspi_programming_summary.md`.
- Run flashes only from `nvidia_sdk/JetPack_6.2.2_Linux_JETSON_ORIN_NANO_TARGETS/Linux_for_Tegra`.
- Always run host prerequisites first:
  - `sudo ./tools/l4t_flash_prerequisites.sh`
- Validate recovery state from host USB IDs before flashing:
  - `0955:7523` means APX/recovery mode (flash-ready)
  - `0955:7020` means normal runtime (not flash-ready)
- If target is reachable over SSH and needs recovery mode, use:
  - `sudo reboot forced-recovery` on the target (or equivalent remote command)
- Match board profile to intent:
  - QSPI-only updates: `jetson-orin-nano-devkit-qspi` (`NO_ROOTFS=1`, `EMMC_CFG=flash_t234_qspi.xml`)
  - Rootfs-only APP updates on this NVMe-based Orin Nano: use `flash.sh -k APP jetson-orin-nano-devkit-nvme nvme0n1p1`.
  - Full device flash on this NVMe-based Orin Nano: use `flash.sh jetson-orin-nano-devkit-nvme nvme0n1p1`.
  - Kernel DTB updates: prefer `flash.sh -k <A_kernel-dtb|B_kernel-dtb>` with non-`-qspi` board profile.
  - On this NVMe-based Orin Nano setup, use `jetson-orin-nano-devkit-nvme internal` for direct `A_kernel-dtb` and `B_kernel-dtb` updates with the non-super DTB file `kernel/dtb/tegra234-p3768-0000+p3767-0005-nv.dtb`.
  - Avoid manually mixing `-c bootloader/generic/cfg/flash_t234_qspi.xml` with `nvme0n1p1` for this DTB-only flow; it failed here with `Can not find partition type for a_kernel-dtb`.
- Flash command examples from `Linux_for_Tegra`:
  - QSPI-only flash: `sudo ./flash.sh jetson-orin-nano-devkit-qspi internal`
  - Rootfs-only APP flash to NVMe: `sudo ./flash.sh -k APP jetson-orin-nano-devkit-nvme nvme0n1p1`
  - Full NVMe flash: `sudo ./flash.sh jetson-orin-nano-devkit-nvme nvme0n1p1`
  - Device-tree-only flash to slot A: `sudo ./flash.sh -k A_kernel-dtb jetson-orin-nano-devkit nvme0n1p1`
  - For slot B device-tree updates, replace `A_kernel-dtb` with `B_kernel-dtb`.
  - Validated NVMe DTB update to slot A: `sudo ./flash.sh -k A_kernel-dtb -d kernel/dtb/tegra234-p3768-0000+p3767-0005-nv.dtb jetson-orin-nano-devkit-nvme internal`
  - Validated NVMe DTB update to slot B: `sudo ./flash.sh -k B_kernel-dtb -d kernel/dtb/tegra234-p3768-0000+p3767-0005-nv.dtb jetson-orin-nano-devkit-nvme internal`
- If a custom kernel DTB should be loaded from rootfs, add `FDT /boot/dtb/kernel_tegra234-p3768-0000+p3767-0005-nv.dtb` to `/boot/extlinux/extlinux.conf` and copy the matching DTB into `/boot/dtb/`; otherwise UEFI falls back to the flashed DTB partition.
- Treat `Flashing completed` and `has been flashed successfully` as required success markers.
- After flash, verify board returns to normal boot and network reachability (`192.168.55.1` when applicable).
- Do not start flashing if APX/recovery is not confirmed.
- APX visibility check is necessary but not always sufficient: if `flash.sh` reports empty `ECID` or `Error: probing the target board failed`, run `sudo ./nvautoflash.sh --print_boardid` and require successful board detection before flashing.

## Conventions
- Keep changes narrowly scoped to the requested area; do not refactor unrelated folders.
- Avoid editing vendor/upstream trees unless explicitly requested (for example third-party repositories under `nvidia_sdk/ultralytics/`).
- For device-side command requests, execute on the target device using the workspace skills (`.github/skills/terminal-command-inject` for commands, `.github/skills/scp-file-copy` for file transfer), not on the host shell as a substitute.
- Preserve existing shell-script style and board/spec-driven configuration patterns in Jetson tooling; do not hardcode board IDs when configs already exist.

## Pitfalls
- Serial access on Linux hosts may fail without proper udev/dialout permissions; see `README.md`.
- The Jetson serial login prompt can require a short settle time after entering the username; when automating login on `/dev/ttyACM0`, wait about `2-3s` before sending the password.
- The serial console may present the login prompt as `<hostname> login:` and may remain in a hidden password state after an interrupted attempt; recovering with a control-C plus carriage return before retrying is reliable.
- Host paths and toolchain prerequisites can break Jetson build/flash workflows; verify prerequisites in `.github/copilot-instructions.md` before changing scripts.

## References
- Flash programming guide: `doc/docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/FlashingSupport.html`.

# Copilot instructions for this workspace (Jetson L4T / JetPack 6.2.2)

## Scope and boundaries
- Main editable tree: `JetPack_6.2.2_Linux_JETSON_ORIN_NANO_TARGETS/Linux_for_Tegra`.
- Treat `JetPack_6.2.2_Linux/NVIDIA_Nsight_Perf_SDK` as vendor/sample content; avoid edits unless asked.
- `Linux_for_Tegra/rootfs` is a full Ubuntu snapshot; avoid broad edits there.
- `jetson-orin.txt` is very large decompiled DTS output; use targeted reads/search.
- `ultralytics/` is a separate Git-managed repo (origin: `https://github.com/ultralytics/ultralytics.git`); treat as upstream/vendor and avoid edits unless explicitly requested.

## Big-picture architecture (how flashing is composed)
- Flash flow is layered: `nvsdkmanager_flash.sh` (checks + UX wrapper) -> `nvautoflash.sh` (RCM board detect) -> `flash.sh` (core flashing/signing logic).
- `flash.sh` is the root implementation and supports `flash.sh [options] <target_board> <root_device>`; wrappers should stay thin.
- Board config is shell-source composition, not a manifest system: board files like `jetson-orin-nano-devkit.conf` source `p3767.conf.common` and override functions/vars.
- Board-specific runtime selection happens in functions like `update_flash_args_common` (DTB/BPFDTB/EMMC config from `board_sku` + FAB).
- BUP path is spec-driven: `l4t_generate_soc_bup.sh` reads spec arrays from `jetson_board_spec.cfg` and invokes `build_l4t_bup.sh`, which delegates to `flash.sh --no-flash --sign --bup`.

## Critical workflows (host)
- Default flash from `Linux_for_Tegra`: `sudo ./nvautoflash.sh`.
- Explicit flash path: `sudo ./flash.sh <target_board> <rootdev>`.
- Rootfs-only APP flash for this NVMe Orin Nano: `sudo ./flash.sh -k APP jetson-orin-nano-devkit-nvme nvme0n1p1`.
- Full NVMe flash for this Orin Nano: `sudo ./flash.sh jetson-orin-nano-devkit-nvme nvme0n1p1`.
- Safe prechecks before flashing: `sudo ./nvsdkmanager_flash.sh --check-all` (or `--check-target-only`, `--check-network-only`).
- External storage/initrd flash: `sudo ./nvsdkmanager_flash.sh --storage nvme0n1p1`.
- Rootfs binary sync before image generation: `sudo ./apply_binaries.sh -r ./rootfs`.
- Kernel + NVIDIA OOT build from `source/`: `./nvbuild.sh -o <abs_outdir>`.

## Prerequisites and non-obvious constraints
- Root is required for key scripts (`flash.sh`, `nvautoflash.sh`, `nvsdkmanager_flash.sh`, `apply_binaries.sh`).
- Initrd flash hard-checks host deps (`sshpass`, `abootimg`, `zstd`) and NFS firewall/VPN conditions in `tools/kernel_flash/l4t_initrd_flash.sh`.
- x86 kernel builds require `CROSS_COMPILE` and `${CROSS_COMPILE}gcc` (`source/nvbuild.sh`).
- Source/build paths must not contain spaces or colons (enforced in `source/Makefile`).

## Conventions for edits
- Keep changes in shell style used here: `set -e` / `set -o pipefail`, helper functions, explicit early exits.
- Do not hardcode board SKUs/IDs in scripts when existing spec/config already models them (`jetson_board_spec.cfg`, board `.conf`, `p3767.conf.common`).
- If behavior is user-facing, prefer wrapper-layer updates (`nvsdkmanager_flash.sh`, `nvautoflash.sh`) and only touch `flash.sh` for core mechanics.
- USB recovery detection is vendor/product scanning under `/sys/bus/usb/devices` in both `nvautoflash.sh` and `tools/kernel_flash/l4t_initrd_flash.sh`; keep logic aligned.
- Keep signing/secure boot flows centralized (`l4t_sign_image.sh`, `flash.sh`, BUP scripts); avoid one-off signing code.

## Workspace operating defaults
- Device defaults used by workspace skills and automation:
  - `target_ip`: `192.168.55.1`
  - `target_user`: `ubuntu`
  - `target_password`: `ubuntu`
  - `target_ssh_private_key`: `~/.ssh/id_ed25519` (host path; create it if missing and copy public key to target)
  - `target_serial_device`: `/dev/ttyACM0`
  - `target_prompt_regex`: `(?:<username>@<username>:.*[$#]|[$#]) ?$`
- Per top-level `README.md`, current device-side workflow often uses `.github/skills/terminal-command-inject` and `.github/skills/scp-file-copy`.

## Device command routing (skills only)
- **Important:** Device operations must use the workspace skills, not host-local shell commands.
- `target_serial_device` (`/dev/ttyACM0`) is a serial console path and should be treated as the fallback path when SSH-based command execution is not available.
- Requests that say "on device", "in device", or target `192.168.55.1` should use `.github/skills/terminal-command-inject`, which is SSH-first and can fall back to serial when needed.
- File copy, deploy, and copy-then-run workflows should use `.github/skills/scp-file-copy`.
- For commands requiring privilege (for example `sudo ls /home/ -al`), execute them remotely through the SSH-first skill and return the remote output.
- When the workspace is using password-based SSH access, prefer non-interactive `sshpass`/`scp` style execution or an equivalent non-interactive password injection path; do not rely on an interactive `sudo` password prompt because it can leave the terminal waiting indefinitely.
- Host `bash` is only for host-side operations; never use it as a substitute for device-side command requests.

## Tool availability preflight
- Before running any device-side request, load the relevant workspace skill and use the defaults defined in this file.
- If the SSH path fails because of missing credentials or connectivity, follow the skill's retry flow and then use serial fallback if appropriate.
- When serial automation starts from a `login:` prompt, prefer the terminal-command skill's serial runner path that waits briefly after the username before writing the password.
- For `/dev/ttyACM0`, prefer carriage return for login/password submission even if shell commands use another line ending.
- Do not silently fall back to host-local execution for device commands.
