# ภาพหลักฐานพร้อมส่ง — Lab 04 (ENG29 2121)

โฟลเดอร์นี้จัดภาพส่งอาจารย์ **ตามแถวของ rubric 10 คะแนน** ทุกภาพเป็นภาพจริงจากแอปที่รันอยู่
ไม่ได้วาดหรือตัดต่อ และตัวเลขบนภาพมาจาก ngspice-47 จริง (run id อยู่ในแบนเนอร์ของทุกภาพ)

- แอป: `http://127.0.0.1:5002/simulate` (Flask, `debug=False`)
- เบราว์เซอร์อัตโนมัติ: **Playwright MCP 0.0.86** (Microsoft Edge, headless)
- เอนจิน: **ngspice-47** เรียกผ่าน `PATH` (ไม่ได้ตั้ง `NGSPICE_BIN`)
- โมเดล BJT: `models/2N3904_onsemi.model` (onsemi 2N3904) — **NOT instructor verified**
- วันที่เก็บหลักฐาน: 2026-11-24

---

## แถวที่ 1 · ความต่อเนื่องจาก Lab 3 (1 คะแนน)

| ไฟล์ | สิ่งที่พิสูจน์ |
| --- | --- |
| `01-lab3-divider.png` | Lab 3 โหมด Voltage Divider ยังทำงาน: IC **1.23 mA**, VCE **8.05 V** ตรงกับ Lab 02 |
| `01-lab3-fixed.png` | โหมด Fixed Bias: IC **1.13 mA**, VCE **9.51 V** |
| `01-lab3-emitter.png` | โหมด Emitter Bias: IC **1.03 mA**, VCE **8.71 V** |
| `01-lab3-regression-playwright.png` | เปิดหน้า Lab 3 ผ่าน Playwright MCP: ค่า 1.23 mA / 8.05 V ยังอยู่ครบ (regression ผ่าน) — เทสต์ Lab 3 ทั้ง 23 ตัวยังผ่าน |

## แถวที่ 2 · การเชื่อม ngspice (3 คะแนน)

| ไฟล์ | สิ่งที่พิสูจน์ |
| --- | --- |
| `02-ngspice-dc-op.png` | `.op` สำเร็จจริง: `Success — .op completed (1/1)`, `ngspice exit 0`, run `lab04-dc-1rsj5oto`; VB **1.97 V**, VE **1.34 V**, VC **9.08 V**, VCE **7.75 V**, IC **1.33 mA** (จาก `i(vic)`) พร้อม provenance: เอนจิน, โมเดล, ที่มาของโมเดล, netlist และ run id |
| `02-ngspice-dc-re2k.png` | Adapter รับค่าที่เปลี่ยนจริง: RE 1 kΩ → 2 kΩ ให้ IC **0.71 mA**, VCE **8.99 V**, run ใหม่ `lab04-dc-kypyv0r4` (ไม่ใช่ผลค้าง) |
| `02-ngspice-invalid-re-error.png` | Error handling: RE = 0 → `Error — no results shown`, “RE must be > 0 and <= 1e+07”, **0 กราฟ**, ไม่มีสถานะ Success |

หมายเหตุ: ค่า analytical ของ Lab 3 แสดงแยกและติดป้าย “not SPICE” ทุกครั้ง ไม่ถูกนำมาปนกับผล SPICE

## แถวที่ 3 · AC + Transient (2 คะแนน)

| ไฟล์ | สิ่งที่พิสูจน์ |
| --- | --- |
| `03-ac-bode.png` | Bode จาก `.ac` จริง: **141 จุด**, 1 Hz–10 MHz, gain **0.48–4.80 dB**, midband **4.80 dB**, −3 dB ที่ **1.30964 Hz**, phase จุดแรก −127.5° ; แกนมีหน่วย Frequency (Hz, log) / Gain (dB) / Phase (deg) ; run `lab04-ac-qnupv3e6` |
| `03-transient-10mv-1khz.png` | Waveform จาก `.tran` จริง: 10 mV / 1 kHz, **108 จุด**, 0–5 ms, Vin **19.92 mV pp**, Vout **34.60 mV pp**, เฟสกลับด้าน (สหสัมพันธ์ −1.00); run `lab04-tran-8mjz3c9u` |
| `03-transient-20mv-2khz.png` | ปรับ Source แล้วผลตอบสนองจริง: 20 mV / 2 kHz → หน้าต่าง 0–2.5 ms, Vin **39.84 mV pp**, Vout **69.21 mV pp**, run ใหม่ `lab04-tran-mj_x9z2g` |

## แถวที่ 4 · UI และ Impeccable (2 คะแนน)

| ไฟล์ | สิ่งที่พิสูจน์ |
| --- | --- |
| `04-impeccable-before-1280.png` | สภาพหน้าก่อนรอบ polish (หลักฐาน “ก่อน”) |
| [`../B8-impeccable-after-1280.png`](../B8-impeccable-after-1280.png) | หลัง polish ที่ 1280 px: 5 พาเนลเรียงตามงาน, ผลลัพธ์อ่านง่าย, ไม่มี overflow |
| [`../B8-impeccable-after-390.png`](../B8-impeccable-after-390.png) | หลัง polish ที่ 390 px: หนึ่งคอลัมน์ ไม่มี overflow |

Detector ของ Impeccable คืน `[]` (ไม่พบปัญหา) ทั้ง 1280×800 และ 390×844 หลังรอบสุดท้าย
รอบ polish แก้เฉพาะ HTML/CSS + ข้อความ UI **ไม่แตะ** สูตร DC bias, netlist, directive ของ ngspice,
parser, validation หรือค่าของโมเดล — ตัวเลขวิศวกรรมก่อน/หลังเท่ากันทุก run

## แถวที่ 5 · Browser Acceptance (1 คะแนน)

| ไฟล์ | สิ่งที่พิสูจน์ |
| --- | --- |
| `05-browser-acceptance-all-B1-B8.png` | Contact sheet รวม 9 ภาพของ B1–B8 (สร้างจากภาพจริงด้วย Playwright MCP) |
| `05-browser-acceptance-desktop.png` | B8 เดสก์ท็อป 1280 px: `scrollWidth 1280` ไม่มี overflow, 5 พาเนล, กราฟ AC จริง |
| `05-browser-acceptance-mobile.png` | B8 มือถือ 390 px: 390/390 px ไม่มี overflow, ลำดับ DOM เดิม |

B1–B8 ทั้งหมด **PASS** และรันด้วย Playwright MCP จริง (เดิมบันทึกเป็น NOT RUN เพราะยังไม่ได้ติดตั้ง —
รอบนี้ติดตั้งและรันใหม่แล้ว) บันทึกฉบับเต็มอยู่ใน [`../../validation.md`](../../validation.md)

## แถวที่ 6 · GitHub + Reproducibility (1 คะแนน)

| ไฟล์ | สิ่งที่พิสูจน์ |
| --- | --- |
| `06-github-repo.png` | หน้า repository จริงบน GitHub พร้อม README |
| `06-github-commits.png` | ประวัติ commit บน `main` (มีงาน Lab 03 → Lab 04 ต่อเนื่องกัน) |

- Repository: <https://github.com/Khatcharin16/Gitlab>
- ขั้นตอนติดตั้ง/รัน: [`../../../README.md`](../../../README.md)
- บันทึกการตรวจรับทั้งหมด: [`../../validation.md`](../../validation.md)
- หลักฐาน ngspice ดิบ (netlist/log/raw): [`../ce-vendor-model/`](../ce-vendor-model/)

---

## วิธีรันซ้ำ (reproduce)

```powershell
cd C:\Users\B6837006\Documents\GitHub\Gitlab
$env:NGSPICE_BIN = "C:\Users\B6837006\AppData\Local\Programs\ngspice-47\Spice64\bin\ngspice_con.exe"   # หรือปล่อยว่างถ้า ngspice อยู่ใน PATH
.venv\Scripts\python.exe -m app.app
# เปิด http://127.0.0.1:5000/simulate
.venv\Scripts\python.exe -m pytest tests/ -q      # 58 passed
```

## ข้อจำกัดที่ต้องแจ้งอาจารย์ (ไม่อำพราง)

1. **โมเดล BJT ยังไม่ใช่ของ Instructor Starter Kit** — เครื่องนี้ไม่มีไฟล์ Starter Kit (ค้นทั้งเครื่องแล้ว
   ตามบันทึกใน `validation.md`) จึงใช้ onsemi 2N3904 ที่อ้างอิงแหล่งที่มาได้ และติดป้าย
   `unverified — NOT instructor verified` ไว้บนหน้าเว็บทุกจุด ตัวเลขทั้งหมดจึงเป็น “ผล ngspice จริง
   แต่ยังไม่ใช่เลขที่ instructor-verified” — เปลี่ยนเป็นโมเดลอาจารย์ได้ด้วย
   `NGSPICE_MODEL_LINE` หรือ `NGSPICE_MODEL_FILE` แล้วรัน B2–B6 ใหม่
2. **Impeccable dual-agent critique แบบเต็มรูปแบบ** ยังไม่ได้ทำ (NOT RUN) — ที่ทำคือ detector +
   visual review ด้วยตนเอง
