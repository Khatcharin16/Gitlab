# Real ngspice samples used as parser fixtures

These files were produced by `ngspice_con.exe` (ngspice-47, built 2026-08-11)
on 2026-11-24 with:

```
ngspice_con.exe -b -o <name>.log -r <name>.raw <name>.cir
```

| File | Purpose |
| --- | --- |
| `test.cir`, `run.log`, `run.raw` | first DC-only batch spike (ASCII raw format proof) |
| `ac_tran.cir`, `ac_tran.log`, `ac_tran.raw` | AC + transient raw section proof (complex vs real values) |
| `parser_fixture.cir`, `parser_fixture.log`, `parser_fixture.raw` | resistor network using the **same node names** as the Lab 04 CE netlist (`vcc`, `rctop`, `base`, `emitter`, `collector`, `out`, `vs`, `0`) including the `VIC` current-sense source, so `parse_op`, `parse_ac` and `parse_tran` can be tested with real engine output |

**Important:** `parser_fixture.cir` contains no transistor and no instructor
model. It is a parser fixture only, not an engineering result and not a
substitute for the SPICE run of the CE amplifier. The real CE run waits for the
instructor-verified BJT model line in `NGSPICE_MODEL_LINE`.
