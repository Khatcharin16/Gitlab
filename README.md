# Gitlab

ใช้สำหรับเรียนแลบ Compro ไฟฟ้า

DC Circuit Calculator
วัตถุประสงค์: เครื่องมือคำนวณค่าทางไฟฟ้าสำหรับวงจรกระแสตรง (DC) ช่วยคำนวณแรงดัน กระแส ความต้านทาน และกำลังไฟฟ้าของวงจรตัวต้านทานแบบอนุกรม ขนาน และผสม ได้อย่างรวดเร็วและแม่นยำ

ENG29 2121 BJT Common-Emitter DC Bias Web App
A Flask-based web application for calculating the DC operating point of a common-emitter BJT bias circuit.

## Links

- Repository: <https://github.com/Khatcharin16/Gitlab>
- Web app (local): <http://127.0.0.1:5000>
- UI preview: [`docs/ui-preview.png`](docs/ui-preview.png)

## Running the app

```bash
python -m app.app
```

Then open <http://127.0.0.1:5000> in your browser.

Run the tests with:

```bash
python -m pytest tests/
```

## Inputs

- VCC: Power supply voltage (V or mV)
- R1, R2: Voltage divider resistors (Ω, kΩ, or MΩ)
- RC, RE: Collector and emitter resistors (Ω, kΩ, or MΩ)
- beta: Transistor current gain (β)
- VBE: Base-emitter voltage (V or mV)

The dashboard opens with a worked example
(VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ, RE = 1.0 kΩ,
β = 100, VBE = 0.70 V).

## Outputs

- DC operating point: IB, IC, IE, VBE, VCE, VE, VB, VC, VBC
- Region classification: active, cutoff, or saturation
- Independent nodal-solve comparison check

## Development

- Built with Flask, Python 3.10, pytest
- Source: `app/` (routes, engineering logic, templates, static), `tests/`, `docs/`