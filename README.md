# Gitlab

ใช้สำหรับเรียนแลบ Compro ไฟฟ้า

DC Circuit Calculator
วัตถุประสงค์: เครื่องมือคำนวณค่าทางไฟฟ้าสำหรับวงจรกระแสตรง (DC) ช่วยคำนวณแรงดัน กระแส ความต้านทาน และกำลังไฟฟ้าของวงจรตัวต้านทานแบบอนุกรม ขนาน และผสม ได้อย่างรวดเร็วและแม่นยำ

ENG29 2121 BJT Common-Emitter DC Bias Web App
A Flask-based web application for calculating the DC operating point of a common-emitter BJT bias circuit.

## Running the app

```bash
python app\app.py
```

Then open <http://127.0.0.1:5000> in your browser.

## Inputs

- VCC: Power supply voltage (V)
- R1, R2: Voltage divider resistors (Ω)
- RC, RE: Collector and emitter resistors (Ω)
- beta: Transistor current gain (β)
- VBE: Base-emitter voltage (V)

## Outputs

- DC operating point: IB, IC, IE, VBE, VCE, VE, VB, VC, VBC
- Region classification: active, cutoff, or saturation
- Independent nodal-solve comparison check

## Development

- Built with Flask, Python 3.10, pytest
- Source: `app/`, `tests/`, `static/`, `docs/`