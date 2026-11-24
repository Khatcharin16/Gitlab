# Real CE ngspice artifacts — bundled onsemi 2N3904 vendor model

Generated on 2026-11-24 with `ngspice_con.exe` (ngspice-47) using the model
bundled at `models/2N3904_onsemi.model`:

```text
.MODEL Q2n3904 npn IS=1.26532e-10 BF=206.302 NF=1.5 VAF=1000 ...
```

Source: onsemi, <https://www.onsemi.com/download/models/lib/2n3904.lib>
(downloaded 2026-11-24). The file header credits MODPEX / Symmetry Design
Systems.

**These are real ngspice results, but the model is NOT the Instructor Starter
Kit model.** The page labels it
`Bundled vendor model (onsemi 2N3904) — NOT instructor verified`. The model was
chosen because the Starter Kit was not present on this machine; it is a cited
vendor model, not a guessed or hand-tuned one. Replace it with the instructor
`.model` line (`NGSPICE_MODEL_LINE` or `NGSPICE_MODEL_FILE`) before graded use.

| File | Content |
| --- | --- |
| `dc-circuit.cir`, `dc-run.log`, `dc-run.raw` | `.op` run at RE = 1 kΩ |
| `dc-re2k-circuit.cir`, `dc-re2k-run.log`, `dc-re2k-run.raw` | `.op` run at RE = 2 kΩ (B3) |
| `ac-circuit.cir`, `ac-run.log`, `ac-run.raw` | `.ac dec 20 1 10meg` (141 points) |
| `ac-20mv-circuit.cir`, `ac-20mv-run.log`, `ac-20mv-run.raw` | `.ac` at 20 mV excitation, proving gain is amplitude-independent |
| `tran-circuit.cir`, `tran-run.log`, `tran-run.raw` | `.tran` at 10 mV / 1 kHz (108 points, 5 periods) |
| `tran-20mv-2khz-circuit.cir`, `tran-20mv-2khz-run.log`, `tran-20mv-2khz-run.raw` | `.tran` at 20 mV / 2 kHz (B6) |

All runs exited 0. The netlists contain the fixed reference node names
`vcc`, `rctop`, `base`, `emitter`, `collector`, `out`, `vs`, `0`, and the
collector current is read from the zero-volt `VIC` source in series with `RC`.

Observed values (from these artifacts):

| Analysis | Result |
| --- | --- |
| DC, RE = 1 kΩ | VB 1.97 V, VE 1.34 V, VC 9.08 V, VCE 7.75 V, IC 1.33 mA |
| DC, RE = 2 kΩ | VCE 8.99 V, IC 0.71 mA |
| AC | 141 points, 1 Hz–10 MHz, gain 0.48–4.80 dB, midband 4.80 dB, −3 dB at 1.30964 Hz |
| Transient 10 mV / 1 kHz | 108 points, 0–5 ms, Vin pp 19.92 mV, Vout pp 34.60 mV, inverted (r ≈ −1.00) |
| Transient 20 mV / 2 kHz | 108 points, 0–2.5 ms, Vin pp 39.84 mV, Vout pp 69.21 mV |
