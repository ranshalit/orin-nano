#!/usr/bin/env python3

import argparse
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

SKILLS_DIR = Path(__file__).resolve().parents[2]
if str(SKILLS_DIR) not in sys.path:
    sys.path.insert(0, str(SKILLS_DIR))

from common.target_config import load_target_defaults

TARGET_DEFAULTS = load_target_defaults()

DEVICE_IP = TARGET_DEFAULTS.ip
DEFAULT_USER = TARGET_DEFAULTS.user
DEFAULT_PASSWORD = TARGET_DEFAULTS.password

SSH_COMMON_OPTS = [
    "-q",
    "-oLogLevel=ERROR",
    "-oServerAliveInterval=15",
    "-oServerAliveCountMax=3",
    "-oPreferredAuthentications=password,keyboard-interactive",
    "-oPubkeyAuthentication=no",
    "-oPasswordAuthentication=yes",
    "-oKbdInteractiveAuthentication=yes",
    "-oNumberOfPasswordPrompts=1",
    "-oStrictHostKeyChecking=no",
    "-oUserKnownHostsFile=/dev/null",
]


class AuthMode:
    AUTO = "auto"
    KEY = "key"
    SSHPASS = "sshpass"


@dataclass
class CommandSpec:
    command: str
    expect_substring: Optional[str] = None
    expect_regex: Optional[str] = None


@dataclass
class ScpPushSpec:
    local_path: str
    remote_path: str


@dataclass
class ScpPullSpec:
    remote_path: str
    local_path: str


def _print_section_header(title: str) -> None:
    sys.stdout.write("\n" + "=" * 80 + "\n")
    sys.stdout.write(title.rstrip() + "\n")
    sys.stdout.write("=" * 80 + "\n")
    sys.stdout.flush()


def _decode(s: str) -> str:
    return s


def _require_sshpass() -> None:
    if shutil.which("sshpass") is None:
        raise RuntimeError(
            "sshpass is required but was not found. Install it (e.g. `sudo apt-get install sshpass`)."
        )


def _probe_key_auth(user: str, port: int, connect_timeout_seconds: int) -> bool:
    """Return True if key-based, non-interactive SSH works (BatchMode=yes)."""
    ssh_cmd = [
        "ssh",
        "-p",
        str(port),
        *SSH_COMMON_OPTS,
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={int(connect_timeout_seconds)}",
        f"{user}@{DEVICE_IP}",
        "--",
        "true",
    ]
    try:
        completed = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=max(5, int(connect_timeout_seconds) + 5),
        )
        return int(completed.returncode) == 0
    except Exception:
        return False


def _run_scp(
    scp_command: List[str],
    timeout_seconds: int,
) -> Tuple[int, str]:
    try:
        completed = subprocess.run(
            scp_command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        out = (completed.stdout or "") + (completed.stderr or "")
        return int(completed.returncode), out
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") + (e.stderr or "")
        return 124, out + f"\nSCP timed out after {timeout_seconds}s.\n"


def _run_ssh_command(
    user: str,
    port: int,
    command: str,
    connect_timeout_seconds: int,
    timeout_seconds: int,
) -> Tuple[int, str]:
    command_quoted = shlex.quote(command)

    ssh_cmd = [
        "ssh",
        "-p",
        str(port),
        *SSH_COMMON_OPTS,
        "-o",
        f"ConnectTimeout={int(connect_timeout_seconds)}",
        f"{user}@{DEVICE_IP}",
        "--",
        "bash",
        "-lc",
        command_quoted,
    ]

    try:
        completed = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        out = (completed.stdout or "") + (completed.stderr or "")
        return int(completed.returncode), out
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") + (e.stderr or "")
        return 124, out + f"\nTimed out after {timeout_seconds}s.\n"


def _run_scp_with_sshpass(
    scp_command: List[str],
    ssh_password: str,
    timeout_seconds: int,
) -> Tuple[int, str]:
    _require_sshpass()
    # Always supply a password when using sshpass to prevent interactive prompts.
    # Default to the skill's default credentials if caller passed an empty/None value.
    password = ssh_password or DEFAULT_PASSWORD

    # Avoid printing the password or argv anywhere.
    cmd = ["sshpass", "-p", password, *scp_command]
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        out = (completed.stdout or "") + (completed.stderr or "")
        return int(completed.returncode), out
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") + (e.stderr or "")
        return 124, out + f"\nSCP timed out after {timeout_seconds}s.\n"
    except FileNotFoundError:
        return 127, "sshpass not found (cannot use sshpass SCP path).\n"


def _run_ssh_command_with_sshpass(
    user: str,
    ssh_password: str,
    port: int,
    command: str,
    connect_timeout_seconds: int,
    timeout_seconds: int,
) -> Tuple[int, str]:
    _require_sshpass()

    password = ssh_password or DEFAULT_PASSWORD
    # IMPORTANT: ssh receives a *command string*, not an argv vector. Even when we
    # supply a list to subprocess.run(), ssh will concatenate args with spaces.
    # Without quoting, `bash -lc <command>` would only consume the first word of
    # <command>. Quote the entire command string so bash receives it intact.
    command_quoted = shlex.quote(command)

    ssh_cmd = [
        "ssh",
        "-p",
        str(port),
        *SSH_COMMON_OPTS,
        "-o",
        f"ConnectTimeout={int(connect_timeout_seconds)}",
        f"{user}@{DEVICE_IP}",
        "--",
        "bash",
        "-lc",
        command_quoted,
    ]

    # Avoid printing the password or argv anywhere.
    cmd = ["sshpass", "-p", password, *ssh_cmd]
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        out = (completed.stdout or "") + (completed.stderr or "")
        return int(completed.returncode), out
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or "") + (e.stderr or "")
        return 124, out + f"\nTimed out after {timeout_seconds}s.\n"


def _check_expectations(spec: CommandSpec, output: str) -> Optional[str]:
    if spec.expect_substring:
        if spec.expect_substring not in output:
            return f"Expected substring not found: {spec.expect_substring!r}"
    if spec.expect_regex:
        if not re.search(spec.expect_regex, output, flags=re.MULTILINE):
            return f"Expected regex not matched: {spec.expect_regex!r}"
    return None


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run SSH commands and SCP transfers against the target configured in "
            f"{TARGET_DEFAULTS.source_file}, capturing output and stopping based on results."
        ),
    )

    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="SSH password from target defaults")
    parser.add_argument(
        "--sudo-password",
        default=None,
        help="sudo password (defaults to --password)",
    )
    parser.add_argument("--port", type=int, default=22)

    parser.add_argument(
        "--command",
        action="append",
        default=[],
        help="Command to run on the device (repeatable)",
    )
    parser.add_argument(
        "--expect",
        action="append",
        default=[],
        help="Expected substring for the corresponding --command (repeatable)",
    )
    parser.add_argument(
        "--expect-regex",
        action="append",
        default=[],
        help="Expected regex for the corresponding --command (repeatable)",
    )

    parser.add_argument(
        "--scp-push",
        nargs=2,
        action="append",
        default=[],
        metavar=("LOCAL_PATH", "REMOTE_PATH"),
        help="Copy local path to device (repeatable)",
    )
    parser.add_argument(
        "--scp-pull",
        nargs=2,
        action="append",
        default=[],
        metavar=("REMOTE_PATH", "LOCAL_PATH"),
        help="Copy device path to local path (repeatable)",
    )
    parser.add_argument(
        "--scp-recursive",
        action="store_true",
        help="Use recursive scp (-r) for directory transfers",
    )

    parser.add_argument("--connect-timeout", type=int, default=30)
    parser.add_argument("--command-timeout", type=int, default=60)
    parser.add_argument(
        "--scp-timeout",
        type=int,
        default=300,
        help="Timeout for each scp operation in seconds",
    )

    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue even if a command fails or expectations are not met",
    )

    parser.add_argument(
        "--auth",
        choices=[AuthMode.AUTO, AuthMode.KEY, AuthMode.SSHPASS],
        default=AuthMode.AUTO,
        help="Authentication mode: auto (try SSH keys then sshpass), key (SSH keys only), sshpass (password only)",
    )

    args = parser.parse_args(list(argv))

    if not str(DEVICE_IP or "").strip():
        raise SystemExit("Missing target config: `target_ip`. Ask in Copilot chat and update .github/copilot-instructions.md, or pass/set host config.")
    if not str(args.user or "").strip():
        raise SystemExit("Missing target config: `target_user`. Ask in Copilot chat and update .github/copilot-instructions.md, or pass --user.")
    if not str(args.password or "").strip():
        raise SystemExit("Missing target config: `target_password`. Ask in Copilot chat and update .github/copilot-instructions.md, or pass --password.")

    if args.sudo_password is None:
        args.sudo_password = args.password

    if args.expect and len(args.expect) != len(args.command):
        raise SystemExit("--expect must be provided exactly once per --command (or omit it).")
    if args.expect_regex and len(args.expect_regex) != len(args.command):
        raise SystemExit("--expect-regex must be provided exactly once per --command (or omit it).")

    if not args.command and not args.scp_push and not args.scp_pull:
        raise SystemExit("No actions provided. Add --command and/or --scp-push/--scp-pull.")

    return args


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)

    # Build specs
    command_specs: List[CommandSpec] = []
    for i, cmd in enumerate(args.command):
        expect_sub = args.expect[i] if args.expect else None
        expect_re = args.expect_regex[i] if args.expect_regex else None
        command_specs.append(CommandSpec(command=cmd, expect_substring=expect_sub, expect_regex=expect_re))

    scp_push_specs = [ScpPushSpec(local, remote) for (local, remote) in args.scp_push]
    scp_pull_specs = [ScpPullSpec(remote, local) for (remote, local) in args.scp_pull]

    # Determine authentication approach.
    if args.auth == AuthMode.KEY:
        use_key = True
    elif args.auth == AuthMode.SSHPASS:
        use_key = False
    else:
        use_key = _probe_key_auth(args.user, args.port, args.connect_timeout)

    if use_key:
        sys.stdout.write("Auth: key (BatchMode=yes)\n")
        sys.stdout.flush()
    else:
        sys.stdout.write("Auth: sshpass (password)\n")
        sys.stdout.flush()
        try:
            _require_sshpass()
        except Exception as e:
            sys.stderr.write(str(e).rstrip() + "\n")
            if args.auth == AuthMode.AUTO:
                sys.stderr.write(
                    f"Tip: configure SSH keys for {args.user}@{DEVICE_IP} or install sshpass for password-based automation.\n"
                )
            return 127

    # SCP first (pre-deploy), then SSH commands.
    scp_base = [
        "scp",
        "-P",
        str(args.port),
        *SSH_COMMON_OPTS,
        "-o",
        f"ConnectTimeout={int(args.connect_timeout)}",
    ]
    if args.scp_recursive:
        scp_base.insert(1, "-r")

    for spec in scp_push_specs:
        _print_section_header(f"SCP PUSH: {spec.local_path} -> {args.user}@{DEVICE_IP}:{spec.remote_path}")
        scp_cmd = [
            *scp_base,
            spec.local_path,
            f"{args.user}@{DEVICE_IP}:{spec.remote_path}",
        ]
        if use_key:
            rc, out = _run_scp(scp_cmd, timeout_seconds=args.scp_timeout)
        else:
            rc, out = _run_scp_with_sshpass(scp_cmd, ssh_password=args.password, timeout_seconds=args.scp_timeout)
        sys.stdout.write(out)
        sys.stdout.flush()
        if rc != 0 and not args.continue_on_error:
            sys.stderr.write(f"\nSCP push failed with exit code {rc}. Stopping.\n")
            if "Permission denied" in out:
                sys.stderr.write("Tip: check username/password or configure SSH keys; you can force with --auth.\n")
            return rc

    for spec in scp_pull_specs:
        _print_section_header(f"SCP PULL: {args.user}@{DEVICE_IP}:{spec.remote_path} -> {spec.local_path}")
        scp_cmd = [
            *scp_base,
            f"{args.user}@{DEVICE_IP}:{spec.remote_path}",
            spec.local_path,
        ]
        if use_key:
            rc, out = _run_scp(scp_cmd, timeout_seconds=args.scp_timeout)
        else:
            rc, out = _run_scp_with_sshpass(scp_cmd, ssh_password=args.password, timeout_seconds=args.scp_timeout)
        sys.stdout.write(out)
        sys.stdout.flush()
        if rc != 0 and not args.continue_on_error:
            sys.stderr.write(f"\nSCP pull failed with exit code {rc}. Stopping.\n")
            if "Permission denied" in out:
                sys.stderr.write("Tip: check username/password or configure SSH keys; you can force with --auth.\n")
            return rc

    if command_specs:
        _print_section_header(f"SSH COMMANDS: {args.user}@{DEVICE_IP}")
        for idx, spec in enumerate(command_specs, start=1):
            _print_section_header(f"COMMAND {idx}: {spec.command}")
            if use_key:
                rc, out = _run_ssh_command(
                    user=args.user,
                    port=args.port,
                    command=spec.command,
                    connect_timeout_seconds=args.connect_timeout,
                    timeout_seconds=args.command_timeout,
                )
            else:
                rc, out = _run_ssh_command_with_sshpass(
                    user=args.user,
                    ssh_password=args.password,
                    port=args.port,
                    command=spec.command,
                    connect_timeout_seconds=args.connect_timeout,
                    timeout_seconds=args.command_timeout,
                )

            sys.stdout.write(out)
            sys.stdout.flush()

            expectation_error = _check_expectations(spec, out)
            if expectation_error:
                sys.stderr.write("\n" + expectation_error + "\n")
                if not args.continue_on_error:
                    sys.stderr.write("Stopping due to expectation failure.\n")
                    return 2

            if rc != 0:
                sys.stderr.write(f"\nCommand exit code: {rc}\n")
                if "Permission denied" in out:
                    sys.stderr.write("Tip: check username/password or configure SSH keys; you can force with --auth.\n")
                if not args.continue_on_error:
                    sys.stderr.write("Stopping due to non-zero exit code.\n")
                    return rc

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
