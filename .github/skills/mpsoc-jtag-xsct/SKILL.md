````skill
---
name: mpsoc-jtag-xsct
description: 'Connect to Xilinx/AMD MPSoC UltraScale+ over JTAG and perform allowed debug operations using XSDB/XSCT (target select, connect, dow, con/stop, read/write memory, read/write registers, and scripted sessions). Use when asked to run JTAG commands, inspect target state, load ELF/bitstream, poke memory/registers, or automate XSCT debug flows.'
---

# MPSoC UltraScale+ JTAG (XSDB / XSCT)

This skill handles host-side debug/control operations on AMD/Xilinx MPSoC UltraScale+ targets over JTAG using `xsdb` and `xsct`.

Use this skill for requests like:

- "connect to zynq ultrascale+ with jtag"
- "run xsdb/xsct commands"
- "download elf via dow"
- "read/write memory or registers"
- "script a jtag debug session"

## Scope

Allowed operations over JTAG include:

- Start tool sessions (`xsdb`, `xsct`)
- Connect/disconnect to hw server (`connect`, `disconnect`)
- Enumerate/select targets (`targets`, `target`)
- Run control (`con`, `stop`, `rst`, `after`)
- Download artifacts (`dow <elf>`, optional `fpga -file <bit/bin>` where applicable)
- Memory access (`mrd`, `mwr`)
- Register access (`rrd`, `rwr`)
- Breakpoints/watchpoints and status inspection
- Scripted execution with `.tcl` files via `xsct <script.tcl>` or here-doc

If user asks for unsupported/unsafe board actions (for example permanent flash programming) and it is not explicitly requested, ask for confirmation first.

## Inputs (ask only if missing)

- Board/SoC family and expected target core (A53/R5/PMU/MicroBlaze)
- JTAG adapter presence and expected cable index (if multiple)
- Artifact paths (ELF, bitstream, Tcl script) when needed
- Required transport:
  - local cable via `connect`
  - remote hw_server via `connect -url <host>:3121`

## Preflight

1. Verify tools are installed: `command -v xsdb xsct`.
2. Verify JTAG/hw_server visibility:
   - local: `xsdb -eval "connect; targets"`
   - remote: `xsdb -eval "connect -url <host>:3121; targets"`
3. If multiple targets are listed, identify and select the intended one before `dow`/R/W operations.

## Standard command patterns

### Quick one-liners

- Enumerate targets:

  `xsdb -eval "connect; targets"`

- Select target + stop + download + run:

  `xsdb -eval "connect; targets -set -filter {name =~ \"*A53*#0\"}; stop; dow ./app.elf; con"`

- Read/write memory:

  `xsdb -eval "connect; targets -set -filter {name =~ \"*A53*#0\"}; mrd 0xFF5E0200 4; mwr 0xFF5E0200 0x00000001"`

- Read/write registers:

  `xsdb -eval "connect; targets -set -filter {name =~ \"*A53*#0\"}; rrd cpsr; rwr x0 0x1234"`

### Scripted session (`xsct`)

Example `session.tcl`:

```tcl
connect
targets
targets -set -filter {name =~ "*A53*#0"}
stop
dow ./app.elf
mrd 0xFF5E0200 4
rwr x0 0x1234
con
```

Run with:

`xsct ./session.tcl`

## Execution policy

- Execute only user-requested JTAG actions.
- Confirm before destructive operations (reset loops, flash/program commands, mass writes).
- For read/write operations, echo exact address/register and value in result summary.
- Return transcript grouped by action: connect, target-select, download, run-control, memory/register I/O.

## Troubleshooting

- `cannot connect to hw_server`: ensure cable/board powered, `hw_server` running, and URL/port correct.
- `no targets found`: check JTAG chain, adapter permissions, cable index, and board boot mode.
- `dow` fails: verify ELF matches architecture/core and target is halted.
- Register name errors: use architecture-correct register names for selected target.

## Notes

- Prefer explicit target filters before any `dow`, `mwr`, or `rwr`.
- For repeatable flows, use Tcl scripts checked into repo and invoke with `xsct`.

````