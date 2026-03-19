# Project Guidelines

## Scope
- This root workspace includes documentation archives, downloaded NVIDIA bundles, and active development under `nvidia_sdk/`.
- Prefer edits in source/config/workflow files, not large binary artifacts (for example `*.tbz2`, model weights, generated run outputs).
- If the task targets Jetson flashing, kernel work, or device operations, follow `nvidia_sdk/.github/copilot-instructions.md` as the authoritative project-specific guide.

## Architecture
- Root-level layout:
  - `doc/`: mirrored/reference documentation.
  - `nvidia_download/`: downloaded SDK metadata and archives.
  - `nvidia_sdk/`: active project area (JetPack/L4T tools, skills, scripts, and experiments).
- Treat `nvidia_sdk/JetPack_6.2.2_Linux_JETSON_ORIN_NANO_TARGETS/Linux_for_Tegra` as the main editable Jetson platform tree.

## Build And Test
- No single workspace-wide build/test command exists at the root.
- For Jetson flashing/build flows, run commands from `nvidia_sdk/JetPack_6.2.2_Linux_JETSON_ORIN_NANO_TARGETS/Linux_for_Tegra` and use documented commands in:
  - `nvidia_sdk/.github/copilot-instructions.md`
  - `nvidia_sdk/README.md`
- Before running expensive operations, prefer targeted checks and dry-run style validation where available.

## Conventions
- Keep changes narrowly scoped to the requested area; do not refactor unrelated folders.
- Avoid editing vendor/upstream trees unless explicitly requested (for example third-party repositories under `nvidia_sdk/ultralytics/`).
- For device-side command requests, execute on the target device (SSH MCP route when available), not on the host shell as a substitute.
- Preserve existing shell-script style and board/spec-driven configuration patterns in Jetson tooling; do not hardcode board IDs when configs already exist.

## Pitfalls
- Serial access on Linux hosts may fail without proper udev/dialout permissions; see `nvidia_sdk/README.md`.
- Host paths and toolchain prerequisites can break Jetson build/flash workflows; verify prerequisites in `nvidia_sdk/.github/copilot-instructions.md` before changing scripts.

## References
- Flash programming guide: `doc/docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/FlashingSupport.html`.
