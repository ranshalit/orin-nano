# General

This isjetson orin nano kit.
doc/ folder contains user guide, e.g. flash support can be found in doc/docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/FlashingSupport.html

# build

1. used sdk manager for first flash programing
2. then do everything on device (installs, updates, demos, etc)

## previous installs and tests
installed ultralytics, tested with GPU:

source ~/yolo-venv/bin/activate
>>> import ultralytics
>>> import torch
>>> ultralytics.cuda.is_available()

yolo predict model=yolo11n.pt source=0 conf=0.25 save=True project=~/yolo-runs name=camera-test exist_ok=True show=True

# skills
using .github skills of terminal-command-inject and copy scp-copy-files skill for testing and working with the device (target)

## SSH-MCP (installed for this workspace)
- Source: `tools/ssh-mcp` (cloned from `https://github.com/mixelpixx/SSH-MCP`)
- Build output: `nvidia_sdk/tools/ssh-mcp/build/index.js`
- Workspace MCP config: `.vscode/mcp.json`
- Tracked SSH key profile: `.vscode/ssh-mcp.profile.json`
- Copilot CLI note: put MCP JSON config under `~/.copilot/` so the CLI can load it.

### How SSH MCP server was added
Use this in Copilot CLI: `copilot` -> `/mcp add` (the command is interactive; there is not a documented full inline `/mcp add ...` form).

Enter:
- Name: `ssh-server`
- Command: `node`
- Args: `/media/ranshal/jetson/orin/nvidia_sdk/tools/ssh-mcp/build/index.js`
- Env: `NODE_NO_WARNINGS=1`

Press `Ctrl+S` to save.

If prompted for SSH defaults in your server flow, use `.vscode/ssh-mcp.profile.json` values:
- `host`: `192.168.55.1`
- `port`: `22`
- `username`: `ubuntu`
- `privateKeyPath`: `~/.ssh/id_ed25519`

### SSH key usage
Use `ssh_connect` with the defaults from `.vscode/ssh-mcp.profile.json`:
- `host`: `192.168.55.1`
- `port`: `22`
- `username`: `ubuntu`
- `privateKeyPath`: `~/.ssh/id_ed25519`

## Serial console permissions (`/dev/ttyACM*` and `/dev/ttyUSB*`)
If serial access fails with permission denied, use this host udev rule file:

`/etc/udev/rules.d/99-jetson-serial.rules`

```udev
SUBSYSTEM=="tty", KERNEL=="ttyACM*", GROUP="dialout", MODE="0666", TAG+="uaccess"
SUBSYSTEM=="tty", KERNEL=="ttyUSB*", GROUP="dialout", MODE="0666", TAG+="uaccess"
```

Reload and apply:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=tty
```

This sets mode `0666` for matching serial devices while keeping group `dialout`.

## Serial login timing (`/dev/ttyACM0`)
When the Jetson serial console is sitting at `login:`, automatic login is timing-sensitive.

- After sending `ubuntu`, wait about `2-3s` before sending the password.
- Sending the password immediately can leave the serial automation stuck before the shell prompt appears.
- The terminal-command serial runner now includes this delay automatically; if needed, adjust it with `--post-username-delay <seconds>`.
- This console may show the prompt as `ubuntu login:` instead of bare `login:`.
- Login/password submission is more reliable with carriage return than with line feed on `/dev/ttyACM0`.
- If an interrupted attempt leaves the console in a hidden password state, send `Ctrl+C` and then `Enter` to recover the visible login prompt before retrying.


# TODO
add list_serial to tools
rm .copilot/mcp (i prefer it to be local in repo)
understand the syntax of cmd args etc
change into relative files

## Flash connectivity troubleshooting (March 2026)
- `0955:7523` in `lsusb` means APX is enumerated, but flashing can still fail if board probing does not complete.
- Symptom: `flash.sh` shows empty `ECID` and `Error: probing the target board failed`.
- Confirm actual flash readiness with:
	- `sudo ./nvautoflash.sh --print_boardid`
- If it reports `0 connections found`, re-enter forced recovery, reconnect USB-C (prefer direct host port), and retry probe before flashing.