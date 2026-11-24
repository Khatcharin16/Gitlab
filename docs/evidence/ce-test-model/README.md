# Real CE ngspice artifacts — TEST MODEL ONLY

Generated on 2026-11-24 with `ngspice_con.exe` (ngspice-47) using:

```
.model QTEST NPN(IS=1e-14 BF=100)
```

`set via NGSPICE_MODEL_LINE`, labelled `NGSPICE_MODEL_SOURCE=TEST ONLY - not instructor verified`.

**These are plumbing/browser-acceptance artifacts, not instructor-verified engineering results.**
The model parameters were chosen only to exercise netlist generation, the batch engine and the
ASCII raw parser. They are deliberately not stored in application code. Replace the environment
variable with the instructor Starter Kit `.model` line before using the simulator for graded
results.

| File | Content |
| --- | --- |
| `dc-circuit.cir`, `dc-run.log`, `dc-run.raw` | `.op` run, ASCII raw operating point |
| `ac-circuit.cir`, `ac-run.log`, `ac-run.raw` | `.ac dec 20 1 10meg` run (141 points) |
| `tran-circuit.cir`, `tran-run.log`, `tran-run.raw` | `.tran` run (108 points, 5 periods of 1 kHz) |

All three exited 0. The netlists contain the fixed reference node names
`vcc`, `base`, `emitter`, `collector`, `out`, `vs`, `0`.
