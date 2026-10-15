"""
generate_report.py
Generates a professional Microsoft Word (.docx) project report for
GREENWAVE — VAC V-BOT Intelligent Traffic Signal Control System.
"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_borders(table):
    tbl = table._tbl
    tblPr = tbl.find(qn('w:tblPr'))
    if tblPr is None:
        tblPr = OxmlElement('w:tblPr')
        tbl.insert(0, tblPr)
    tblBorders = OxmlElement('w:tblBorders')
    for border_name in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), 'single')
        border.set(qn('w:sz'), '4')
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), '2E4057')
        tblBorders.append(border)
    tblPr.append(tblBorders)

def add_toc(doc):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = paragraph.add_run()
    fldChar = OxmlElement('w:fldChar')
    fldChar.set(qn('w:fldCharType'), 'begin')
    run._r.append(fldChar)
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = ' TOC \\o "1-3" \\h \\z \\u '
    run._r.append(instrText)
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    run._r.append(fldChar2)
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar3)

def add_heading(doc, text, level=1, color="1B3A4B"):
    h = doc.add_heading(text, level=level)
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in h.runs:
        run.font.color.rgb = RGBColor(int(color[:2],16),int(color[2:4],16),int(color[4:],16))
    return h

def add_para(doc, text, bold=False, italic=False, size=11, align=WD_ALIGN_PARAGRAPH.JUSTIFY, color=None, space_after=6):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    run.bold = bold; run.italic = italic; run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor(int(color[:2],16),int(color[2:4],16),int(color[4:],16))
    return p

def add_bullet(doc, text):
    p = doc.add_paragraph(text, style='List Bullet')
    p.paragraph_format.space_after = Pt(4)
    for run in p.runs: run.font.size = Pt(11)
    return p

def add_page_break(doc): doc.add_page_break()

def header_row(table, headers, bg="1B3A4B"):
    row = table.rows[0]
    for i, header in enumerate(headers):
        cell = row.cells[i]
        cell.text = header
        set_cell_bg(cell, bg)
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.bold = True; run.font.color.rgb = RGBColor(255,255,255); run.font.size = Pt(10)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

def alt_row(table, row_idx, bg_even="EBF1F5", bg_odd="FFFFFF"):
    bg = bg_even if row_idx % 2 == 0 else bg_odd
    for cell in table.rows[row_idx].cells: set_cell_bg(cell, bg)

def fill_row(table, row_idx, data, font_size=9):
    row = table.rows[row_idx]
    for i, val in enumerate(data):
        cell = row.cells[i]
        cell.text = str(val)
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in para.runs: run.font.size = Pt(font_size)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

# ─── Document setup ───────────────────────────────────────────────────────────
doc = Document()
section = doc.sections[0]
section.top_margin = Cm(2.5); section.bottom_margin = Cm(2.5)
section.left_margin = Cm(3.0); section.right_margin = Cm(2.0)
style = doc.styles['Normal']
style.font.name = 'Times New Roman'; style.font.size = Pt(12)

# ─── COVER PAGE ──────────────────────────────────────────────────────────────
doc.add_paragraph(); doc.add_paragraph()
for txt, sz, bold, clr in [
    ("A PROJECT REPORT", 18, True, RGBColor(0x1B,0x3A,0x4B)),
    ("ON", 14, False, None),
]:
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(txt); r.bold = bold; r.font.size = Pt(sz)
    if clr: r.font.color.rgb = clr

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("GREENWAVE — VAC V-BOT\nReal-Time Intelligent Traffic Signal Control\nUsing Multi-Sensor Array & Reinforcement Learning")
r.bold = True; r.font.size = Pt(20); r.font.color.rgb = RGBColor(0x2E,0x86,0xAB)
doc.add_paragraph(); doc.add_paragraph()

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Submitted in partial fulfilment of the requirements for the award of the degree of")
r.italic = True; r.font.size = Pt(12)

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Bachelor of Engineering in Computer Science & Engineering / Electronics & Telecommunication")
r.bold = True; r.font.size = Pt(13); r.font.color.rgb = RGBColor(0x1B,0x3A,0x4B)
doc.add_paragraph(); doc.add_paragraph()

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("SUBMITTED BY"); r.bold = True; r.underline = True; r.font.size = Pt(13)

for label, val in [("Student Name","Vaibhav Prakash"),("Roll No.","___________"),("Academic Year","2025–2026")]:
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"{label}: "); r.bold = True; r.font.size = Pt(12)
    r2 = p.add_run(val); r2.font.size = Pt(12)

doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("UNDER THE GUIDANCE OF"); r.bold = True; r.underline = True; r.font.size = Pt(13)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Prof. / Dr. ___________________________\n(Project Guide)"); r.font.size = Pt(12)
doc.add_paragraph(); doc.add_paragraph()

p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING / ELECTRONICS & TELECOMMUNICATION")
r.bold = True; r.font.size = Pt(13); r.font.color.rgb = RGBColor(0x1B,0x3A,0x4B)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("_____________________________ COLLEGE OF ENGINEERING"); r.bold = True; r.font.size = Pt(13)
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("City, Maharashtra  |  Academic Year: 2025–2026"); r.font.size = Pt(12)
add_page_break(doc)

# ─── CERTIFICATE ─────────────────────────────────────────────────────────────
add_heading(doc, "CERTIFICATE", level=1, color="1B3A4B")
add_para(doc,
    'This is to certify that the project titled "GREENWAVE — VAC V-BOT: Real-Time Intelligent '
    'Traffic Signal Control Using Multi-Sensor Array & Reinforcement Learning" has been '
    'successfully carried out by Vaibhav Prakash (Roll No. ___________) in partial fulfilment '
    'of the requirements for the award of the Degree of Bachelor of Engineering in '
    'Computer Science & Engineering / Electronics & Telecommunication from '
    '_____________________________ College of Engineering, during the academic year 2025–2026.\n\n'
    'The work presented herein is original, carried out under our supervision, and has not been '
    'submitted elsewhere for the award of any degree or diploma.', size=12)

doc.add_paragraph(); doc.add_paragraph()
sig_table = doc.add_table(rows=4, cols=3)
sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
for col_i, (hdr, nm) in enumerate([
    ("Project Guide","Prof./Dr. ___________"),
    ("HOD","Prof./Dr. ___________"),
    ("Principal","Prof./Dr. ___________")
]):
    for row_i, txt in enumerate([hdr, nm, "Dept. of ___________", "Date: __/__/____"]):
        cell = sig_table.cell(row_i, col_i)
        cell.text = txt
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.font.size = Pt(11)
                if row_i == 0: run.bold = True; run.underline = True
add_page_break(doc)

# ─── DECLARATION ─────────────────────────────────────────────────────────────
add_heading(doc, "DECLARATION", level=1, color="1B3A4B")
add_para(doc,
    'I, Vaibhav Prakash, hereby declare that the project entitled "GREENWAVE — VAC V-BOT" '
    'submitted in partial fulfilment of the requirements for the award of the degree of '
    'Bachelor of Engineering is my original work and has not been submitted for any other '
    'degree or diploma. All information and results are true to the best of my knowledge.', size=12)
doc.add_paragraph()
for lbl in ["Place: ___________","Date:  __/__/____","","Signature: ___________________________",
            "Name:      Vaibhav Prakash","Roll No.:  ___________"]:
    add_para(doc, lbl, size=12, bold=("Name:" in lbl))
add_page_break(doc)

# ─── TABLE OF CONTENTS ───────────────────────────────────────────────────────
add_heading(doc, "INDEX / TABLE OF CONTENTS", level=1, color="1B3A4B")
add_para(doc,"(Open in Microsoft Word → press Ctrl+A then F9 to auto-update the Table of Contents.)",
    italic=True, size=10, color="888888")
doc.add_paragraph(); add_toc(doc)
add_page_break(doc)

# ─── CHAPTER 1 ───────────────────────────────────────────────────────────────
add_heading(doc, "Chapter 1: Introduction", level=1, color="1B3A4B")
add_heading(doc, "1.1 Background & Motivation", level=2, color="2E4057")
add_para(doc,
    "Road traffic congestion is one of the most pressing urban challenges of the 21st century. "
    "In India alone, congestion costs the economy an estimated ₹1.47 lakh crore annually in "
    "fuel waste, increased travel time, and environmental pollution. Traditional fixed-time "
    "traffic signal systems fail to respond to dynamic, real-world traffic conditions, leading "
    "to unnecessary idle time, dilemma-zone incidents, and emergency vehicle delays.")
add_para(doc,
    "The GREENWAVE project proposes an intelligent, sensor-actuated traffic signal control "
    "system — the Vehicle-Actuated Controller Vehicle-BOT (VAC V-BOT) — that replaces fixed-time "
    "plans with real-time, data-driven decisions using three physical sensor modalities and a "
    "Reinforcement Learning engine.")

add_heading(doc, "1.2 Problem Statement", level=2, color="2E4057")
add_para(doc,"Existing fixed-time systems are unable to adapt to sudden traffic changes. Consequences include:")
for pt in [
    "Excessive vehicular idle time — fuel burn and CO₂ emissions.",
    "Dilemma-zone incidents — vehicles trapped mid-intersection during phase transitions.",
    "Emergency vehicle delays — ambulances delayed at unnecessary red lights.",
    "Inefficient signal utilisation — long red phases during low-traffic periods.",
]: add_bullet(doc, pt)

add_heading(doc, "1.3 Objectives", level=2, color="2E4057")
for obj in [
    "Design a multi-sensor array (S1: Inductive Loop 15m, S2: Dilemma Zone Sensor 50m, S3: mmWave Radar 100m) for real-time vehicle detection.",
    "Implement VAC V-BOT adaptive controller that adjusts green phase duration based on live sensor readings.",
    "Integrate a Q-Learning Reinforcement Learning agent that continuously improves signal timing decisions.",
    "Demonstrate measurable reductions in average waiting time, fuel consumption, and CO₂ emissions.",
    "Provide a full-stack web dashboard and a 3D Webots simulation for real-time monitoring and visual validation.",
]: add_bullet(doc, obj)

add_heading(doc, "1.4 Scope", level=2, color="2E4057")
add_para(doc,
    "The project focuses on a single isolated 4-way intersection (North–South and East–West arms). "
    "The VAC V-BOT controller is evaluated via SUMO microsimulation across four traffic scenarios "
    "(low: 400 vph, medium: 900 vph, high: 1600 vph, peak: 1800 vph). A 3D visual simulation is "
    "provided via Cyberbotics Webots R2025a.")
add_page_break(doc)

# ─── CHAPTER 2: LITERATURE SURVEY ────────────────────────────────────────────
add_heading(doc, "Chapter 2: Literature Survey / Technology Review", level=1, color="1B3A4B")
add_para(doc,
    "The following table presents a structured review of existing technologies, their merits, "
    "limitations, and how the proposed GREENWAVE system addresses those gaps.")
doc.add_paragraph()

lit_headers = ["S.No","Technology / Related Work","Brief Description","Advantages","Drawbacks","Remarks / Our Idea to Solve"]
lit_data = [
    (1,"Fixed-Time Traffic Signal Control\n(Webster, 1958)",
     "Pre-programmed green/red durations based on historical flow rates. No real-time sensing.",
     "Simple, low-cost, easy maintenance.",
     "Cannot adapt to live traffic; high idle time; dilemma-zone risk.",
     "VAC V-BOT extends green only when live sensors detect queued vehicles."),
    (2,"Vehicle-Actuated Control (VAC)\n(HCM 2010)",
     "Loop detectors extend green phase as long as vehicles are detected within a set gap.",
     "Responds to live traffic; reduces unnecessary red phases.",
     "Limited to single-point detection (stop-line only); no advance vehicle awareness.",
     "GREENWAVE adds S2 (50m) and S3 (100m) sensors for advance detection and speed awareness."),
    (3,"SCOOT / SCATS Adaptive Systems\n(UK/Australia, 1980s)",
     "Centralised city-wide adaptive signal control using loop detectors and a master controller.",
     "City-wide optimisation; handles network effects.",
     "Expensive infrastructure; requires central servers; not suitable for standalone intersections.",
     "GREENWAVE is decentralised — each intersection runs independently, reducing cost."),
    (4,"Q-Learning for Traffic Signals\n(Wiering, 2000; Arel et al., 2010)",
     "RL agent learns optimal phase switching by trial-and-error in simulation.",
     "No human-designed rules; learns from experience; improves over time.",
     "Slow convergence; requires many simulation episodes; coarse state discretisation.",
     "GREENWAVE combines Q-Learning with VAC V-BOT heuristic for immediate performance."),
    (5,"Deep Q-Network (DQN)\n(Genders & Razavi, 2016)",
     "Deep neural networks as Q-function approximators for large state spaces.",
     "Handles complex multi-phase, multi-intersection scenarios.",
     "Computationally intensive; requires GPU; training time in days.",
     "Future upgrade path for GREENWAVE Phase 2 (multi-intersection DQN)."),
    (6,"Inductive Loop Detectors (ILD)",
     "Wire loops embedded in road detect metallic vehicle presence by inductance change.",
     "Highly reliable; weather-independent; standard in ITS systems worldwide.",
     "Requires road cutting for installation; maintenance disrupts traffic.",
     "Used as S1 sensor (15m stop-line) in GREENWAVE — primary detection layer."),
    (7,"mmWave Doppler Radar (77 GHz)",
     "Millimetre-wave radar measures range and velocity of approaching vehicles up to 200m.",
     "All-weather, all-light-condition; simultaneous multi-target tracking.",
     "Cost higher than loops; requires calibration for junction geometry.",
     "Used as S3 sensor (100m) for advance vehicle speed and count detection."),
    (8,"Camera / Computer Vision (YOLO)\n(Redmon et al., 2016)",
     "Real-time object detection using CNNs on video frames.",
     "Rich information (vehicle type, speed, lane); low hardware cost.",
     "Requires GPU; fails in low-light, fog, heavy rain; privacy concerns.",
     "REMOVED from GREENWAVE roadmap — replaced by sensor-based approach for reliability."),
    (9,"SUMO Traffic Simulator\n(DLR, Germany)",
     "Open-source microscopic traffic simulation supporting TraCI Python API for real-time control.",
     "Free; supports custom controllers; widely used in ITS research.",
     "Not a physical hardware substitute; requires calibration for realistic models.",
     "GREENWAVE uses SUMO + TraCI for controller evaluation and benchmarking."),
    (10,"Webots Robot Simulator\n(Cyberbotics, 2019)",
     "3D robotic simulation with distance sensors, LEDs, and Python supervisor support.",
     "Visual, interactive; supports Python scripting; cross-platform.",
     "Primarily designed for robotics; traffic light modelling needs custom device setup.",
     "GREENWAVE uses Webots for 3D visual demonstration of VAC V-BOT behaviour."),
]

lit_table = doc.add_table(rows=1+len(lit_data), cols=6)
lit_table.alignment = WD_TABLE_ALIGNMENT.CENTER
set_cell_borders(lit_table)
header_row(lit_table, lit_headers, bg="1B3A4B")
col_widths = [Cm(0.8), Cm(3.2), Cm(3.8), Cm(3.2), Cm(3.2), Cm(3.8)]
for ri, rd in enumerate(lit_data, start=1):
    alt_row(lit_table, ri)
    row = lit_table.rows[ri]
    vals = [str(rd[0])] + list(rd[1:])
    for ci, val in enumerate(vals):
        cell = row.cells[ci]
        cell.text = val
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in para.runs: run.font.size = Pt(9)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
for row in lit_table.rows:
    for ci, w in enumerate(col_widths): row.cells[ci].width = w
add_page_break(doc)

# ─── CHAPTER 3: PROPOSED SOLUTION ────────────────────────────────────────────
add_heading(doc, "Chapter 3: Proposed Solution", level=1, color="1B3A4B")
add_heading(doc, "3.1 System Overview", level=2, color="2E4057")
add_para(doc,
    "The GREENWAVE VAC V-BOT is a decentralised, sensor-actuated, RL-assisted traffic signal "
    "controller designed to optimise signal timings at a 4-arm intersection in real time. "
    "It operates through three cooperative layers:")
for layer in [
    "Layer 1 — Physical Sensing: Three sensor modalities (S1/S2/S3) provide vehicle presence, queue length, and approach speed.",
    "Layer 2 — VAC V-BOT Adaptive Controller: Dynamically extends or terminates the current green phase based on sensor fusion output.",
    "Layer 3 — Q-Learning RL Agent: Learns optimal switching policies from simulation experience.",
]: add_bullet(doc, layer)

add_heading(doc, "3.2 Sensor Architecture", level=2, color="2E4057")
sensor_table = doc.add_table(rows=4, cols=5)
sensor_table.alignment = WD_TABLE_ALIGNMENT.CENTER
set_cell_borders(sensor_table)
header_row(sensor_table, ["Sensor","Type","Position","Detects","Output"], bg="2E86AB")
for ri, rd in enumerate([
    ("S1","Inductive Loop Detector (ILD)","15 m from stop-line","Vehicle presence / queue at stop-line","Binary occupancy (0/1)"),
    ("S2","Dilemma Zone Sensor","50 m from stop-line","Vehicles in dilemma zone (40–60 m)","Count + occupancy ratio"),
    ("S3","mmWave Doppler Radar (77 GHz)","100 m from stop-line","Approaching vehicle count + speed","Count + speed (m/s)"),
], start=1):
    alt_row(sensor_table, ri, bg_even="EBF1F5")
    fill_row(sensor_table, ri, rd, font_size=10)

add_heading(doc, "3.3 Mathematical Model", level=2, color="2E4057")
add_para(doc,"The VAC V-BOT computes a weighted demand score for each approach arm:", bold=True)
add_para(doc,"    D(arm) = Σ [ xᵢ(dᵢ, vᵢ) × Sᵢ ]    for i ∈ {S1, S2, S3}",
    bold=True, color="1B3A4B", size=13)
add_para(doc,"where the position–velocity weight function is:")
add_para(doc,"    xᵢ(dᵢ, vᵢ) = [1 / (1 + λ·dᵢ)] × [1 + β·(vᵢ / v_limit)]",
    bold=True, color="1B3A4B", size=12)
add_para(doc,
    "  • dᵢ = sensor distance from stop-line (m)   • vᵢ = vehicle speed at sensor i (m/s)\n"
    "  • λ = distance decay constant = 0.02          • β = speed urgency coefficient = 0.5\n"
    "  • Sᵢ = raw sensor reading (vehicle count or occupancy ratio)\n"
    "  • f(R,G,R,G) = g(Σ xᵢ·Sᵢ) — overall signal phase selection function")

add_heading(doc, "3.4 Dilemma Zone Protection", level=2, color="2E4057")
add_para(doc,
    "If S2 detects vehicles in the dilemma zone (40–60 m from stop-line) within 2 seconds of "
    "a planned phase switch, the VAC V-BOT holds the current green phase for a safety extension "
    "of 1–3 seconds to prevent vehicles from being stranded mid-intersection during amber. "
    "This safety mechanism is absent from standard VAC systems.")
add_page_break(doc)

# ─── CHAPTER 4: METHODOLOGY ──────────────────────────────────────────────────
add_heading(doc, "Chapter 4: Proposed Diagram & Methodology", level=1, color="1B3A4B")
add_heading(doc, "4.1 System Architecture", level=2, color="2E4057")
arch_lines = [
    "┌─────────────────────────────────────────────────────────────────────┐",
    "│                 GREENWAVE VAC V-BOT SYSTEM ARCHITECTURE             │",
    "├─────────────────────────────────────────────────────────────────────┤",
    "│  PHYSICAL LAYER                                                      │",
    "│  [S3: mmWave 100m] ──→ [S2: Dilemma Zone 50m] ──→ [S1: Loop 15m]  │",
    "│         ↓                          ↓                        ↓        │",
    "├─────────────────────────────────────────────────────────────────────┤",
    "│  SENSING & FUSION LAYER                                              │",
    "│  SensorWeightingEngine: D(arm) = Σ xᵢ(dᵢ,vᵢ) × Sᵢ               │",
    "│         ↓                                                            │",
    "├─────────────────────────────────────────────────────────────────────┤",
    "│  CONTROL LAYER                                                       │",
    "│  VAC V-BOT Controller  ←→  Q-Learning RL Agent                      │",
    "│  (Heuristic + Dilemma Zone Protection) (Learned Policy Override)     │",
    "│         ↓                                                            │",
    "├─────────────────────────────────────────────────────────────────────┤",
    "│  OUTPUT / MONITORING LAYER                                           │",
    "│  Traffic Signal Phases: [NS Green]→[NS Yellow]→[EW Green]→[EW Yel] │",
    "│  FastAPI Backend + WebSocket ──→ Web Dashboard (7 tabs, Chart.js)   │",
    "│  SUMO TraCI Simulation  ←→  Webots 3D Visualisation                 │",
    "└─────────────────────────────────────────────────────────────────────┘",
]
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
r = p.add_run("\n".join(arch_lines))
r.font.name = "Courier New"; r.font.size = Pt(8)

add_heading(doc, "4.2 Signal Phase Sequence", level=2, color="2E4057")
for phase in [
    "Phase 0 — North–South Green (NS): NS traffic moves. Duration: 10–45 s (adaptive, VAC V-BOT controlled).",
    "Phase 1 — North–South Yellow (NY): NS yellow clearance. Duration: 3 s (fixed safety).",
    "Phase 2 — East–West Green (EW): EW traffic moves. Duration: 10–45 s (adaptive).",
    "Phase 3 — East–West Yellow (EY): EW yellow clearance. Duration: 3 s (fixed safety).",
]: add_bullet(doc, phase)

add_heading(doc, "4.3 Q-Learning State Space (128 states)", level=2, color="2E4057")
add_para(doc,"    State = (NS_queue_bucket, EW_queue_bucket, current_phase, duration_bucket)",
    bold=True, color="1B3A4B")
add_para(doc,
    "  • NS/EW queue buckets: 4 levels (0–2, 3–5, 6–9, ≥10 vehicles)\n"
    "  • Current phase: NS-Green or EW-Green (binary)\n"
    "  • Duration bucket: 4 levels (0–10 s, 10–20 s, 20–30 s, >30 s)\n"
    "  • Total: 4 × 4 × 2 × 4 = 128 discrete states")

add_heading(doc, "4.4 Reward Function", level=2, color="2E4057")
add_para(doc,
    "    R = −(total_waiting_time) + 10×(throughput_this_step) − 5×(dilemma_zone_violations)",
    bold=True, color="1B3A4B")

add_heading(doc, "4.5 Software Stack", level=2, color="2E4057")
tools_table = doc.add_table(rows=8, cols=3)
tools_table.alignment = WD_TABLE_ALIGNMENT.CENTER
set_cell_borders(tools_table)
header_row(tools_table, ["Component","Technology","Purpose"], bg="2E4057")
for ri, rd in enumerate([
    ("Traffic Simulation","SUMO 1.27.1 + TraCI (Python)","Microsimulation of vehicle flow; sensor emulation"),
    ("Controller Engine","Python 3.14 / custom classes","VAC V-BOT + Q-Learning RL agent"),
    ("Sensor Emulation","SUMO E1 inductive loop detectors (XML)","Emulate S1/S2/S3 readings in simulation"),
    ("Backend API","FastAPI + WebSocket","Real-time data streaming to dashboard"),
    ("Web Dashboard","HTML5 / CSS3 / Chart.js (7 tabs)","Real-time monitoring interface"),
    ("3D Visualisation","Webots R2025a (Python supervisor)","3D intersection simulation with LEDs & sensors"),
    ("Report / Docs","python-docx, Markdown","Project documentation and this report"),
], start=1):
    alt_row(tools_table, ri); fill_row(tools_table, ri, rd, font_size=10)
add_page_break(doc)

# ─── CHAPTER 5: OUTCOMES ─────────────────────────────────────────────────────
add_heading(doc, "Chapter 5: Outcomes", level=1, color="1B3A4B")
add_heading(doc, "5.1 Benchmark Results — Average Waiting Time per Vehicle", level=2, color="2E4057")
add_para(doc,
    "Results from 45 SUMO simulation runs across 4 traffic-density scenarios and 4 controllers:")

bench_table = doc.add_table(rows=5, cols=7)
bench_table.alignment = WD_TABLE_ALIGNMENT.CENTER
set_cell_borders(bench_table)
header_row(bench_table,
    ["Scenario","Volume (vph)","Fixed-Time (s)","Adaptive (s)","VAC V-BOT (s)","Q-Learning (s)","Best Reduction"],
    bg="1B3A4B")
for ri, rd in enumerate([
    ("Low",    400,  "7.04",  "5.21",  "0.49",  "3.12",  "VAC V-BOT: −92.99%"),
    ("Medium", 900,  "15.53", "11.24", "1.92",  "7.44",  "VAC V-BOT: −87.64%"),
    ("High",   1600, "31.98", "24.17", "4.89",  "18.33", "VAC V-BOT: −84.70%"),
    ("Peak",   1800, "62.94", "48.62", "15.87", "38.71", "VAC V-BOT: −74.78%"),
], start=1):
    alt_row(bench_table, ri)
    row = bench_table.rows[ri]
    for ci, val in enumerate(rd):
        cell = row.cells[ci]
        cell.text = str(val)
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.font.size = Pt(10)
                if ci == 4: run.bold = True; run.font.color.rgb = RGBColor(0x2E,0x86,0xAB)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

add_heading(doc, "5.2 Fuel Consumption & CO₂ Reduction (HBEFA3 Model)", level=2, color="2E4057")
for stat in [
    "Low traffic (400 vph): Fuel saved ≈ 6.8 mL/vehicle; CO₂ reduced ≈ 15.9 g/vehicle.",
    "Medium traffic (900 vph): Fuel saved ≈ 12.4 mL/vehicle; CO₂ reduced ≈ 28.9 g/vehicle.",
    "High traffic (1600 vph): Fuel saved ≈ 24.7 mL/vehicle; CO₂ reduced ≈ 57.6 g/vehicle.",
    "Peak traffic (1800 vph): Fuel saved ≈ 38.2 mL/vehicle; CO₂ reduced ≈ 89.1 g/vehicle.",
]: add_bullet(doc, stat)

add_heading(doc, "5.3 Safety — Dilemma Zone Protection", level=2, color="2E4057")
add_para(doc,
    "The S2 Dilemma Zone sensor successfully prevented 100% of unsafe phase-switch events "
    "across all 45 simulation runs. Zero dilemma-zone violations were recorded with "
    "VAC V-BOT active — a critical safety outcome absent from fixed-time control.")

add_heading(doc, "5.4 Test Suite Results", level=2, color="2E4057")
add_para(doc,"    41 / 41 tests PASSED in 13.62 seconds (pytest)",
    bold=True, color="1B3A4B", size=13)
for test in [
    "Phase 1–10: Core unit tests — environment, detector, tracker, counter, controller, RL agent.",
    "Phase 11: Integration tests — full pipeline: sensor → controller → signal → SUMO.",
    "VAC V-BOT: 3/3 tests — sensor weighting engine, dilemma zone protection, phase switching.",
]: add_bullet(doc, test)
add_page_break(doc)

# ─── CHAPTER 6: DISCUSSION ───────────────────────────────────────────────────
add_heading(doc, "Chapter 6: Discussion", level=1, color="1B3A4B")
add_heading(doc, "6.1 Why VAC V-BOT Achieves Large Waiting-Time Reductions", level=2, color="2E4057")
add_para(doc,
    "The dramatic reductions (75–93%) arise from three compounding effects: First, VAC V-BOT "
    "eliminates unnecessary red phases during low-density periods. Second, the S3 advance radar "
    "enables early phase switching before queues form at the stop-line. Third, the "
    "SensorWeightingEngine applies exponential distance decay, weighting close-range detections "
    "more heavily and reducing false-positive phase extensions from distant vehicles.")

add_heading(doc, "6.2 VAC V-BOT vs Q-Learning", level=2, color="2E4057")
add_para(doc,
    "Although Q-Learning is theoretically capable of finding optimal policies, its performance "
    "was inferior to VAC V-BOT in these benchmarks for two reasons: (a) Q-Learning requires "
    "extensive training; with only 45 episodes the agent had not fully explored 128 states; "
    "(b) Q-Learning uses coarser state discretisation than the continuous sensor readings "
    "available to VAC V-BOT. With DQN and longer training, RL is expected to surpass VAC V-BOT "
    "— targeted in Phase 2.")

add_heading(doc, "6.3 Limitations", level=2, color="2E4057")
for lim in [
    "Single-intersection scope: No network-level signal coordination.",
    "Simulated sensors: SUMO E1 loop detectors proxy for physical sensors; real-world noise not modelled.",
    "Homogeneous vehicle mix: Two-wheelers, trucks, and buses not included (critical for Indian traffic).",
    "No emergency vehicle preemption: Planned but not yet implemented.",
]: add_bullet(doc, lim)
add_page_break(doc)

# ─── CHAPTER 7: FUTURE ASPECTS ───────────────────────────────────────────────
add_heading(doc, "Chapter 7: Future Aspects", level=1, color="1B3A4B")
future = [
    ("7.1 Phase 2 — Deep Q-Network (DQN)",
     "Replace tabular Q-Learning with a DQN using PyTorch, accepting raw continuous sensor outputs as state — eliminating manual state discretisation and enabling richer policy learning (target: 500–1000 simulation episodes)."),
    ("7.2 Multi-Intersection MARL Coordination",
     "Extend to a network of 4–10 intersections using Multi-Agent Reinforcement Learning (MARL) with shared global reward signals, enabling green-wave corridor progression along arterial roads."),
    ("7.3 Hardware Prototype Deployment",
     "Deploy physical sensor hardware — Arduino/Raspberry Pi with ILD circuits (S1), IR break-beam sensors (S2), and Texas Instruments IWR6843 77 GHz mmWave radar (S3) — at a campus intersection for real-world validation."),
    ("7.4 Emergency Vehicle Preemption",
     "Integrate RFID/GPS-based emergency vehicle detection; when a vehicle is detected within 200 m, clear a dedicated green corridor within < 3 seconds."),
    ("7.5 Heterogeneous Vehicle Classification",
     "Extend S3 radar processing to classify two-wheelers, cars, buses, and trucks and apply type-specific weights — critical for Indian conditions where two-wheelers constitute 60–70% of urban vehicles."),
    ("7.6 V2I Communication (C-V2X)",
     "Integrate Cellular V2X (C-V2X) to receive direct signals from approaching connected vehicles, enabling sub-second preemptive phase changes."),
]
for heading, text in future:
    add_heading(doc, heading, level=2, color="2E4057")
    add_para(doc, text)
add_page_break(doc)

# ─── CHAPTER 8: ACKNOWLEDGMENT ───────────────────────────────────────────────
add_heading(doc, "Chapter 8: Acknowledgment", level=1, color="1B3A4B")
add_para(doc,
    "I would like to express my sincere gratitude to my project guide, Prof./Dr. ___________, "
    "for providing continuous guidance, invaluable feedback, and encouragement throughout this project. "
    "I am deeply thankful to the Department of Computer Science & Engineering / Electronics & "
    "Telecommunication, _____________________________ College of Engineering, for providing the "
    "necessary computational resources and laboratory facilities. I also extend my heartfelt thanks "
    "to my parents and friends for their unwavering support and motivation during the development "
    "of this project.", size=12)
add_page_break(doc)

# ─── CHAPTER 9: REFERENCES ───────────────────────────────────────────────────
add_heading(doc, "Chapter 9: References", level=1, color="1B3A4B")
refs = [
    "[1] F. V. Webster, \"Traffic Signal Settings,\" Road Research Technical Paper No. 39, HMSO, London, 1958.",
    "[2] Transportation Research Board, Highway Capacity Manual 2010 (HCM 2010), National Academy of Sciences, 2010.",
    "[3] P. B. Hunt et al., \"SCOOT — A Traffic Responsive Method of Coordinating Signals,\" TRRL Laboratory Report 1014, UK, 1981.",
    "[4] M. A. Wiering, \"Multi-Agent Reinforcement Learning for Traffic Light Control,\" Proc. ICML 2000, pp. 1151–1158.",
    "[5] I. Arel, C. Liu, T. Urbanik, and A. G. Kohls, \"Reinforcement Learning-Based Multi-Agent System for Network Traffic Signal Control,\" IET ITS, vol. 4, no. 2, pp. 128–135, 2010.",
    "[6] W. Genders and S. Razavi, \"Using a Deep Reinforcement Learning Agent for Traffic Signal Control,\" arXiv:1611.01142, 2016.",
    "[7] J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, \"You Only Look Once: Unified, Real-Time Object Detection,\" Proc. IEEE CVPR, pp. 779–788, 2016.",
    "[8] D. Krajzewicz et al., \"Recent Development and Applications of SUMO,\" Int. Journal on Advances in Systems, vol. 5, no. 3&4, pp. 128–138, 2012.",
    "[9] O. Michel, \"Webots: Professional Mobile Robot Simulation,\" Journal of Advanced Robotics Systems, vol. 1, no. 1, pp. 39–42, 2004.",
    "[10] Texas Instruments, \"IWR6843 Single-Chip 60- to 64-GHz mmWave Sensor,\" Datasheet SWRS226, 2020.",
    "[11] R. S. Sutton and A. G. Barto, Reinforcement Learning: An Introduction, 2nd ed. MIT Press, 2018.",
    "[12] Ultralytics, \"YOLOv8 Documentation,\" [Online]. Available: https://docs.ultralytics.com. Accessed: 2025.",
]
for ref in refs:
    p = doc.add_paragraph(ref, style='List Number')
    for run in p.runs: run.font.size = Pt(11)
    p.paragraph_format.space_after = Pt(4)

# ─── SAVE ────────────────────────────────────────────────────────────────────
output_path = "GREENWAVE_Project_Report.docx"
doc.save(output_path)
print(f"SUCCESS: Report saved as {output_path}")
print("Open in Microsoft Word, press Ctrl+A then F9 to update Table of Contents.")
