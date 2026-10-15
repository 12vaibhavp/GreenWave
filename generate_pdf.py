"""
generate_pdf.py  —  Generates GREENWAVE_Project_Report.pdf using ReportLab.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas

W, H = A4
MARGIN_L = 3.0*cm
MARGIN_R = 2.0*cm
MARGIN_T = 2.5*cm
MARGIN_B = 2.5*cm

# ── Colours ──────────────────────────────────────────────────────────────────
C_DARK  = colors.HexColor('#1B3A4B')
C_BLUE  = colors.HexColor('#2E86AB')
C_MID   = colors.HexColor('#2E4057')
C_LIGHT = colors.HexColor('#EBF1F5')
C_WHITE = colors.white
C_BLACK = colors.black
C_GREEN = colors.HexColor('#27AE60')
C_RED   = colors.HexColor('#C0392B')

# ── Styles ───────────────────────────────────────────────────────────────────
SS = getSampleStyleSheet()

def S(name, **kw):
    base = SS.get(name, SS['Normal'])
    return ParagraphStyle(
        name + '_custom_' + str(id(kw)),
        parent=base, **kw
    )

cover_title   = S('Title',   fontName='Helvetica-Bold', fontSize=26, textColor=C_BLUE,
                  alignment=TA_CENTER, spaceAfter=6, leading=32)
cover_sub     = S('Normal',  fontName='Helvetica-Bold', fontSize=14, textColor=C_DARK,
                  alignment=TA_CENTER, spaceAfter=4)
cover_normal  = S('Normal',  fontName='Helvetica', fontSize=11, textColor=C_BLACK,
                  alignment=TA_CENTER, spaceAfter=4)
cover_label   = S('Normal',  fontName='Helvetica-Bold', fontSize=12, textColor=C_DARK,
                  alignment=TA_CENTER, spaceAfter=2)
ch_heading    = S('Heading1',fontName='Helvetica-Bold', fontSize=16, textColor=C_DARK,
                  spaceAfter=10, spaceBefore=14, leading=20)
sub_heading   = S('Heading2',fontName='Helvetica-Bold', fontSize=13, textColor=C_MID,
                  spaceAfter=6, spaceBefore=10, leading=16)
sub2_heading  = S('Heading3',fontName='Helvetica-Bold', fontSize=11, textColor=C_BLUE,
                  spaceAfter=4, spaceBefore=6)
body          = S('Normal',  fontName='Times-Roman', fontSize=11, leading=16,
                  alignment=TA_JUSTIFY, spaceAfter=6)
body_bold     = S('Normal',  fontName='Times-Bold',  fontSize=11, leading=16,
                  alignment=TA_JUSTIFY, spaceAfter=6)
code_style    = S('Normal',  fontName='Courier', fontSize=8, leading=11,
                  alignment=TA_LEFT, spaceAfter=4, textColor=C_DARK)
math_style    = S('Normal',  fontName='Courier-Bold', fontSize=11, leading=14,
                  alignment=TA_LEFT, spaceAfter=6, textColor=C_DARK,
                  leftIndent=1.5*cm)
bullet_style  = S('Normal',  fontName='Times-Roman', fontSize=11, leading=15,
                  alignment=TA_JUSTIFY, spaceAfter=4, leftIndent=1.2*cm,
                  firstLineIndent=-0.5*cm)
tbl_header    = S('Normal',  fontName='Helvetica-Bold', fontSize=9, textColor=C_WHITE,
                  alignment=TA_CENTER, leading=12)
tbl_cell      = S('Normal',  fontName='Times-Roman', fontSize=9, leading=12,
                  alignment=TA_LEFT)
tbl_cell_ctr  = S('Normal',  fontName='Times-Roman', fontSize=9, leading=12,
                  alignment=TA_CENTER)
tbl_cell_bold = S('Normal',  fontName='Times-Bold',  fontSize=9, leading=12,
                  alignment=TA_CENTER, textColor=C_BLUE)
ref_style     = S('Normal',  fontName='Times-Roman', fontSize=10, leading=14,
                  alignment=TA_JUSTIFY, spaceAfter=4, leftIndent=1.2*cm,
                  firstLineIndent=-1.2*cm)

def B(txt): return f'<b>{txt}</b>'
def I(txt): return f'<i>{txt}</i>'
def C(txt, c): return f'<font color="{c}">{txt}</font>'

def bullet(text):
    return Paragraph(f'• {text}', bullet_style)

def hr(): return HRFlowable(width='100%', thickness=1, color=C_LIGHT, spaceAfter=4, spaceBefore=4)

# ── Table helpers ─────────────────────────────────────────────────────────────
def make_table(headers, rows, col_widths, alt_bg=True):
    hrow = [Paragraph(h, tbl_header) for h in headers]
    data = [hrow]
    for ri, row in enumerate(rows):
        bg = C_LIGHT if (ri % 2 == 0 and alt_bg) else C_WHITE
        data.append([Paragraph(str(c), tbl_cell) for c in row])

    style = [
        ('BACKGROUND', (0,0), (-1,0), C_DARK),
        ('TEXTCOLOR',  (0,0), (-1,0), C_WHITE),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,0), 9),
        ('ALIGN',      (0,0), (-1,0), 'CENTER'),
        ('VALIGN',     (0,0), (-1,-1),'TOP'),
        ('GRID',       (0,0), (-1,-1), 0.5, C_MID),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [C_LIGHT, C_WHITE]),
        ('LEFTPADDING',  (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING',   (0,0), (-1,-1), 3),
        ('BOTTOMPADDING',(0,0), (-1,-1), 3),
    ]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(style))
    return t


# ── Page number footer ────────────────────────────────────────────────────────
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        page = self._pageNumber
        if page <= 3: return   # skip cover/certificate/declaration
        self.setFont('Helvetica', 8)
        self.setFillColor(colors.grey)
        self.drawRightString(W - MARGIN_R, 1.5*cm, f'Page {page} of {page_count}')
        self.drawString(MARGIN_L, 1.5*cm, 'GREENWAVE — VAC V-BOT Project Report')
        self.setLineWidth(0.5)
        self.setStrokeColor(C_LIGHT)
        self.line(MARGIN_L, 1.8*cm, W - MARGIN_R, 1.8*cm)


# ── Build content ─────────────────────────────────────────────────────────────
story = []

# ── COVER PAGE ────────────────────────────────────────────────────────────────
story.append(Spacer(1, 1.5*cm))
story.append(Paragraph('A PROJECT REPORT', S('Normal', fontName='Helvetica-Bold',
    fontSize=16, textColor=C_DARK, alignment=TA_CENTER, spaceAfter=2)))
story.append(Paragraph('ON', S('Normal', fontName='Helvetica', fontSize=13,
    alignment=TA_CENTER, spaceAfter=10)))

story.append(HRFlowable(width='90%', thickness=2, color=C_BLUE, spaceAfter=12, spaceBefore=4))
story.append(Paragraph('GREENWAVE — VAC V-BOT', cover_title))
story.append(Paragraph('Real-Time Intelligent Traffic Signal Control', cover_sub))
story.append(Paragraph('Using Multi-Sensor Array &amp; Reinforcement Learning', cover_sub))
story.append(HRFlowable(width='90%', thickness=2, color=C_BLUE, spaceAfter=16, spaceBefore=8))

story.append(Spacer(1, 0.5*cm))
story.append(Paragraph(I('Submitted in partial fulfilment of the requirements for the award of the degree of'), cover_normal))
story.append(Paragraph(B('Bachelor of Engineering'), cover_sub))
story.append(Paragraph(B('Computer Science &amp; Engineering / Electronics &amp; Telecommunication'), cover_sub))
story.append(Spacer(1, 0.8*cm))

story.append(Paragraph(B('SUBMITTED BY'), cover_label))
info_table = Table([
    [Paragraph(B('Student Name'), tbl_cell), Paragraph('Vaibhav Prakash', tbl_cell)],
    [Paragraph(B('Roll No.'),     tbl_cell), Paragraph('___________', tbl_cell)],
    [Paragraph(B('Academic Year'),tbl_cell), Paragraph('2025–2026', tbl_cell)],
], colWidths=[6*cm, 8*cm])
info_table.setStyle(TableStyle([
    ('ALIGN', (0,0),(-1,-1),'LEFT'),
    ('FONTSIZE',(0,0),(-1,-1),11),
    ('TOPPADDING',(0,0),(-1,-1),3),
    ('BOTTOMPADDING',(0,0),(-1,-1),3),
]))
story.append(info_table)
story.append(Spacer(1, 0.6*cm))

story.append(Paragraph(B('UNDER THE GUIDANCE OF'), cover_label))
story.append(Paragraph('Prof. / Dr. ___________________________', cover_normal))
story.append(Paragraph('(Project Guide)', cover_normal))
story.append(Spacer(1, 0.8*cm))

story.append(HRFlowable(width='90%', thickness=1, color=C_DARK, spaceAfter=8, spaceBefore=4))
story.append(Paragraph(B('DEPARTMENT OF COMPUTER SCIENCE &amp; ENGINEERING /'), cover_sub))
story.append(Paragraph(B('ELECTRONICS &amp; TELECOMMUNICATION'), cover_sub))
story.append(Paragraph(B('_____________________________ COLLEGE OF ENGINEERING'), cover_sub))
story.append(Paragraph('City, Maharashtra  |  Academic Year: 2025–2026', cover_normal))
story.append(PageBreak())

# ── CERTIFICATE ───────────────────────────────────────────────────────────────
story.append(Paragraph('CERTIFICATE', ch_heading))
story.append(hr())
story.append(Paragraph(
    'This is to certify that the project titled <b>"GREENWAVE — VAC V-BOT: Real-Time Intelligent '
    'Traffic Signal Control Using Multi-Sensor Array &amp; Reinforcement Learning"</b> has been '
    'successfully carried out by <b>Vaibhav Prakash</b> (Roll No. ___________) in partial '
    'fulfilment of the requirements for the award of the Degree of Bachelor of Engineering in '
    'Computer Science &amp; Engineering / Electronics &amp; Telecommunication from '
    '_____________________________ College of Engineering, during the academic year 2025–2026.<br/><br/>'
    'The work presented herein is original, carried out under our supervision, and has not been '
    'submitted elsewhere for the award of any degree or diploma.', body))
story.append(Spacer(1, 1.5*cm))

sig_data = [
    [Paragraph(B('Project Guide'), tbl_cell_ctr), Paragraph(B('HOD'), tbl_cell_ctr), Paragraph(B('Principal'), tbl_cell_ctr)],
    [Paragraph('Prof./Dr. ___________', tbl_cell_ctr), Paragraph('Prof./Dr. ___________', tbl_cell_ctr), Paragraph('Prof./Dr. ___________', tbl_cell_ctr)],
    [Paragraph('Dept. of ___________', tbl_cell_ctr), Paragraph('Dept. of ___________', tbl_cell_ctr), Paragraph('___________', tbl_cell_ctr)],
    [Paragraph('Date: __/__/____', tbl_cell_ctr), Paragraph('Date: __/__/____', tbl_cell_ctr), Paragraph('Date: __/__/____', tbl_cell_ctr)],
]
sig_t = Table(sig_data, colWidths=[5*cm, 5*cm, 5*cm])
sig_t.setStyle(TableStyle([
    ('ALIGN',(0,0),(-1,-1),'CENTER'),
    ('FONTSIZE',(0,0),(-1,-1),10),
    ('TOPPADDING',(0,0),(-1,-1),4),
    ('BOTTOMPADDING',(0,0),(-1,-1),4),
    ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
    ('LINEABOVE',(0,0),(-1,0),0.5,colors.grey),
]))
story.append(sig_t)
story.append(PageBreak())

# ── DECLARATION ───────────────────────────────────────────────────────────────
story.append(Paragraph('DECLARATION', ch_heading))
story.append(hr())
story.append(Paragraph(
    'I, <b>Vaibhav Prakash</b>, hereby declare that the project entitled '
    '<b>"GREENWAVE — VAC V-BOT: Real-Time Intelligent Traffic Signal Control Using '
    'Multi-Sensor Array &amp; Reinforcement Learning"</b> submitted in partial fulfilment '
    'of the requirements for the award of the degree of Bachelor of Engineering is my original '
    'work and has not been submitted for any other degree or diploma. All information and results '
    'presented in this report are true to the best of my knowledge and belief.', body))
story.append(Spacer(1, 1.5*cm))
for line in ['Place: ___________', 'Date:  __/__/____', '', 'Signature: ___________________________',
             'Name:      Vaibhav Prakash', 'Roll No.:  ___________']:
    story.append(Paragraph(line, body))
story.append(PageBreak())

# ── TABLE OF CONTENTS ─────────────────────────────────────────────────────────
story.append(Paragraph('INDEX / TABLE OF CONTENTS', ch_heading))
story.append(hr())
toc_data = [
    ('Certificate',                                         'ii'),
    ('Declaration',                                         'iii'),
    ('Chapter 1: Introduction',                             '1'),
    ('  1.1  Background &amp; Motivation',                  '1'),
    ('  1.2  Problem Statement',                            '1'),
    ('  1.3  Objectives',                                   '2'),
    ('  1.4  Scope',                                        '2'),
    ('Chapter 2: Literature Survey / Technology Review',    '3'),
    ('Chapter 3: Proposed Solution',                        '5'),
    ('  3.1  System Overview',                              '5'),
    ('  3.2  Sensor Architecture',                          '5'),
    ('  3.3  Mathematical Model',                           '6'),
    ('  3.4  Dilemma Zone Protection',                      '6'),
    ('Chapter 4: Proposed Diagram &amp; Methodology',       '7'),
    ('  4.1  System Architecture',                          '7'),
    ('  4.2  Signal Phase Sequence',                        '7'),
    ('  4.3  Q-Learning State Space',                       '8'),
    ('  4.4  Reward Function',                              '8'),
    ('  4.5  Software Stack',                               '8'),
    ('Chapter 5: Outcomes',                                 '9'),
    ('  5.1  Benchmark Results — Waiting Time',             '9'),
    ('  5.2  Fuel Consumption &amp; CO₂ Reduction',         '9'),
    ('  5.3  Safety — Dilemma Zone',                        '10'),
    ('  5.4  Test Suite Results',                           '10'),
    ('Chapter 6: Discussion',                               '11'),
    ('Chapter 7: Future Aspects',                           '12'),
    ('Chapter 8: Acknowledgment',                           '13'),
    ('Chapter 9: References',                               '14'),
]
toc_rows = [[Paragraph(title, tbl_cell), Paragraph(pg, tbl_cell_ctr)] for title, pg in toc_data]
toc_t = Table(toc_rows, colWidths=[13*cm, 2*cm])
toc_t.setStyle(TableStyle([
    ('ALIGN',(1,0),(1,-1),'RIGHT'),
    ('FONTSIZE',(0,0),(-1,-1),10),
    ('TOPPADDING',(0,0),(-1,-1),3),
    ('BOTTOMPADDING',(0,0),(-1,-1),3),
    ('LINEBELOW',(0,-1),(-1,-1),0.5,colors.lightgrey),
    ('ROWBACKGROUNDS',(0,0),(-1,-1),[C_LIGHT, C_WHITE]),
]))
story.append(toc_t)
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 1 — INTRODUCTION
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph('Chapter 1: Introduction', ch_heading))
story.append(hr())

story.append(Paragraph('1.1  Background &amp; Motivation', sub_heading))
story.append(Paragraph(
    'Road traffic congestion is one of the most pressing urban challenges of the 21st century. '
    'In India alone, traffic congestion costs the economy an estimated <b>₹1.47 lakh crore annually</b> '
    'in fuel waste, increased travel time, and environmental pollution. Traditional fixed-time '
    'traffic signal systems — which assign pre-programmed green durations independent of actual '
    'vehicle flow — exacerbate this problem by failing to respond to dynamic, real-world traffic conditions.', body))
story.append(Paragraph(
    'The <b>GREENWAVE</b> project proposes an intelligent, sensor-actuated traffic signal control system — '
    'the <b>Vehicle-Actuated Controller Vehicle-BOT (VAC V-BOT)</b> — that replaces fixed-time signal plans '
    'with real-time, data-driven signal decisions. The system integrates three physical sensor modalities '
    '(inductive loop detectors, dilemma zone sensors, and millimetre-wave Doppler radar) with a '
    'Reinforcement Learning (RL) engine to continuously optimise signal timings.', body))

story.append(Paragraph('1.2  Problem Statement', sub_heading))
story.append(Paragraph(
    'Existing traffic signal systems in Indian cities operate on fixed-time plans calibrated from '
    'historical data. These systems cannot adapt to sudden changes in vehicle density. Consequences include:', body))
for pt in [
    '<b>Excessive vehicular idle time</b> — contributing to fuel burn and CO₂ emissions.',
    '<b>Dilemma-zone incidents</b> — vehicles trapped mid-intersection during phase transitions.',
    '<b>Emergency vehicle delays</b> — ambulances, fire tenders delayed at red lights.',
    '<b>Inefficient signal utilisation</b> — unnecessarily long red phases during low-traffic periods.',
]:
    story.append(bullet(pt))

story.append(Paragraph('1.3  Objectives', sub_heading))
for obj in [
    'Design a <b>multi-sensor array</b> (S1: Inductive Loop 15 m, S2: Dilemma Zone Sensor 50 m, S3: mmWave Radar 100 m) for real-time vehicle detection.',
    'Implement the <b>VAC V-BOT adaptive controller</b> that adjusts green phase duration based on live sensor readings.',
    'Integrate a <b>Q-Learning RL agent</b> that continuously improves signal timing decisions through simulation.',
    'Demonstrate measurable reductions in <b>average waiting time, fuel consumption, and CO₂ emissions</b> across four traffic-density scenarios.',
    'Provide a <b>full-stack web dashboard</b> and a <b>3D Webots simulation</b> for real-time monitoring and visual validation.',
]:
    story.append(bullet(obj))

story.append(Paragraph('1.4  Scope', sub_heading))
story.append(Paragraph(
    'The project focuses on a single isolated 4-way intersection (North–South and East–West arms). '
    'The VAC V-BOT controller is evaluated via SUMO microsimulation across four traffic scenarios: '
    'Low (400 vph), Medium (900 vph), High (1600 vph), and Peak (1800 vph). '
    'A 3D visual simulation is provided via Cyberbotics Webots R2025a.', body))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 2 — LITERATURE SURVEY
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph('Chapter 2: Literature Survey / Technology Review', ch_heading))
story.append(hr())
story.append(Paragraph(
    'The following table presents a structured review of existing technologies, their merits, '
    'limitations, and how the proposed GREENWAVE system addresses those gaps.', body))
story.append(Spacer(1, 0.3*cm))

lit_headers = ['S.No', 'Technology /\nRelated Work', 'Brief Description',
               'Advantages', 'Drawbacks', 'Remarks /\nOur Idea to Solve']
lit_rows = [
    ('1','Fixed-Time Signal Control\n(Webster, 1958)',
     'Pre-programmed durations based on historical flow. No real-time sensing.',
     'Simple, low-cost,\neasy maintenance.',
     'Cannot adapt to live traffic; high idle time; dilemma-zone risk.',
     'VAC V-BOT extends green only when live sensors detect queued vehicles.'),
    ('2','Vehicle-Actuated Control (VAC)\n(HCM 2010)',
     'Loop detectors extend green phase as long as vehicles detected within set gap.',
     'Responds to live traffic;\nreduces unnecessary red phases.',
     'Limited to single-point detection (stop-line only); no advance awareness.',
     'GREENWAVE adds S2 (50 m) and S3 (100 m) for advance detection.'),
    ('3','SCOOT / SCATS\n(UK/Australia, 1980s)',
     'Centralised city-wide adaptive signal control using detectors and a master controller.',
     'City-wide optimisation;\nhandles network effects.',
     'Expensive; requires central servers; not suitable for standalone intersections.',
     'GREENWAVE is decentralised — each intersection runs independently.'),
    ('4','Q-Learning for Traffic\n(Wiering 2000;\nArel et al. 2010)',
     'RL agent learns optimal phase switching by trial-and-error in simulation.',
     'No human-designed rules;\nlearns from experience.',
     'Slow convergence; requires many episodes; coarse state discretisation.',
     'GREENWAVE combines Q-Learning with VAC V-BOT for immediate performance.'),
    ('5','Deep Q-Network (DQN)\n(Genders & Razavi 2016)',
     'Deep neural networks as Q-function approximators for large state spaces.',
     'Handles complex multi-phase,\nmulti-intersection scenarios.',
     'Computationally intensive;\nrequires GPU; training takes days.',
     'Future upgrade path for GREENWAVE Phase 2.'),
    ('6','Inductive Loop Detectors (ILD)',
     'Wire loops in road detect metallic vehicles by inductance change.',
     'Highly reliable;\nweather-independent;\nITS standard.',
     'Requires road cutting for installation; maintenance disrupts traffic.',
     'Used as S1 sensor (15 m stop-line) — primary detection layer.'),
    ('7','mmWave Doppler Radar\n(77 GHz)',
     'Millimetre-wave radar measures range and velocity up to 200 m.',
     'All-weather, all-light;\nmulti-target tracking.',
     'Higher cost; requires calibration for junction geometry.',
     'Used as S3 sensor (100 m) for advance speed and count detection.'),
    ('8','Camera / CV (YOLO)\n(Redmon et al. 2016)',
     'Real-time object detection on video frames using CNNs.',
     'Rich info (type, speed, lane);\nlow hardware cost.',
     'Needs GPU; fails in fog/rain/night; privacy concerns.',
     'REMOVED from GREENWAVE — replaced by sensors for reliability.'),
    ('9','SUMO Simulator\n(DLR, Germany)',
     'Open-source microsimulation with TraCI Python API for real-time control.',
     'Free; custom controllers;\nwidely used in research.',
     'Not a physical hardware substitute; needs calibration.',
     'Used for controller evaluation and benchmarking across 45 runs.'),
    ('10','Webots\n(Cyberbotics)',
     '3D robotic simulation with distance sensors, LEDs, Python supervisor support.',
     'Visual, interactive;\nPython scripting; cross-platform.',
     'Primarily for robotics; traffic modelling needs custom device setup.',
     'Used for 3D visual demonstration of VAC V-BOT behaviour.'),
]

lit_widths = [1*cm, 3.2*cm, 3.6*cm, 3*cm, 3.2*cm, 3.5*cm]
story.append(make_table(lit_headers, lit_rows, lit_widths))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 3 — PROPOSED SOLUTION
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph('Chapter 3: Proposed Solution', ch_heading))
story.append(hr())

story.append(Paragraph('3.1  System Overview', sub_heading))
story.append(Paragraph(
    'The GREENWAVE VAC V-BOT is a decentralised, sensor-actuated, RL-assisted traffic signal '
    'controller designed to optimise signal timings at a 4-arm intersection in real time. '
    'It operates through three cooperative layers:', body))
for layer in [
    '<b>Layer 1 — Physical Sensing:</b> Three sensor modalities (S1/S2/S3) provide vehicle presence, queue length, and approach speed.',
    '<b>Layer 2 — VAC V-BOT Adaptive Controller:</b> Dynamically extends or terminates the current green phase based on sensor fusion output.',
    '<b>Layer 3 — Q-Learning RL Agent:</b> Learns optimal switching policies from simulation experience and overrides the VAC heuristic when beneficial.',
]:
    story.append(bullet(layer))

story.append(Paragraph('3.2  Sensor Architecture', sub_heading))
sen_headers = ['Sensor', 'Type', 'Position', 'Detects', 'Output']
sen_rows = [
    ('S1', 'Inductive Loop Detector (ILD)',    '15 m from stop-line',  'Vehicle presence / queue at stop-line', 'Binary occupancy (0/1)'),
    ('S2', 'Dilemma Zone Sensor',              '50 m from stop-line',  'Vehicles in dilemma zone (40–60 m)',    'Count + occupancy ratio'),
    ('S3', 'mmWave Doppler Radar (77 GHz)',    '100 m from stop-line', 'Approaching vehicle count + speed',     'Count + speed (m/s)'),
]
story.append(make_table(sen_headers, sen_rows, [1.5*cm, 4*cm, 3*cm, 4.5*cm, 3.5*cm]))

story.append(Paragraph('3.3  Mathematical Model', sub_heading))
story.append(Paragraph('The VAC V-BOT computes a weighted demand score for each approach arm:', body_bold))
story.append(Paragraph('D(arm) = Σ [ xᵢ(dᵢ, vᵢ) × Sᵢ ]    for i ∈ {S1, S2, S3}', math_style))
story.append(Paragraph('where the position–velocity weight function is:', body))
story.append(Paragraph('xᵢ(dᵢ, vᵢ) = [1 / (1 + λ·dᵢ)] × [1 + β·(vᵢ / v_limit)]', math_style))
for param in [
    'dᵢ  = distance of sensor i from stop-line (m)',
    'vᵢ  = measured vehicle speed at sensor i (m/s)',
    'λ   = distance decay constant = 0.02',
    'β   = speed urgency coefficient = 0.5',
    'Sᵢ  = raw sensor reading (vehicle count or occupancy ratio)',
    'f(R,G,R,G) = g(Σ xᵢ·Sᵢ)  — overall signal phase selection function',
]:
    story.append(Paragraph(param, code_style))

story.append(Paragraph('3.4  Dilemma Zone Protection', sub_heading))
story.append(Paragraph(
    'If S2 detects vehicles in the dilemma zone (40–60 m from stop-line) within 2 seconds of a planned '
    'phase switch, the VAC V-BOT holds the current green phase for a safety extension of 1–3 seconds to '
    'prevent vehicles from being stranded mid-intersection during amber. This critical safety feature is '
    '<b>absent from standard VAC systems</b>.', body))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 4 — METHODOLOGY
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph('Chapter 4: Proposed Diagram &amp; Methodology', ch_heading))
story.append(hr())

story.append(Paragraph('4.1  System Architecture Diagram', sub_heading))
arch = [
    '┌─────────────────────────────────────────────────────────────────────┐',
    '│           GREENWAVE VAC V-BOT — SYSTEM ARCHITECTURE                 │',
    '├─────────────────────────────────────────────────────────────────────┤',
    '│  PHYSICAL LAYER                                                      │',
    '│  [S3: mmWave 100m] ──→ [S2: Dilemma 50m] ──→ [S1: Loop 15m]        │',
    '│       ↓                        ↓                     ↓              │',
    '├─────────────────────────────────────────────────────────────────────┤',
    '│  SENSING & FUSION LAYER                                              │',
    '│  SensorWeightingEngine: D(arm) = Σ xᵢ(dᵢ,vᵢ) × Sᵢ               │',
    '│       ↓                                                              │',
    '├─────────────────────────────────────────────────────────────────────┤',
    '│  CONTROL LAYER                                                       │',
    '│  VAC V-BOT Controller  ←→  Q-Learning RL Agent                      │',
    '│  (Heuristic + Dilemma Protection)  (Learned Policy Override)         │',
    '│       ↓                                                              │',
    '├─────────────────────────────────────────────────────────────────────┤',
    '│  OUTPUT / MONITORING LAYER                                           │',
    '│  Signal Phases: [NS Green]→[NS Yellow]→[EW Green]→[EW Yellow]       │',
    '│  FastAPI + WebSocket ──→ Web Dashboard (7 tabs, Chart.js)           │',
    '│  SUMO TraCI Simulation  ←→  Webots 3D Visualisation                 │',
    '└─────────────────────────────────────────────────────────────────────┘',
]
story.append(Paragraph('<br/>'.join(arch), code_style))

story.append(Paragraph('4.2  Signal Phase Sequence', sub_heading))
for phase in [
    '<b>Phase 0 — North–South Green (NS):</b> NS traffic moves. Duration: 10–45 s (adaptive).',
    '<b>Phase 1 — North–South Yellow (NY):</b> NS clearance. Duration: 3 s (fixed).',
    '<b>Phase 2 — East–West Green (EW):</b> EW traffic moves. Duration: 10–45 s (adaptive).',
    '<b>Phase 3 — East–West Yellow (EY):</b> EW clearance. Duration: 3 s (fixed).',
]:
    story.append(bullet(phase))

story.append(Paragraph('4.3  Q-Learning State Space (128 States)', sub_heading))
story.append(Paragraph('State = (NS_queue_bucket, EW_queue_bucket, current_phase, duration_bucket)', math_style))
for p in [
    'NS/EW queue buckets: 4 levels — (0–2), (3–5), (6–9), (≥10 vehicles)',
    'Current phase: NS-Green or EW-Green (binary — 2 states)',
    'Duration bucket: 4 levels — (0–10 s), (10–20 s), (20–30 s), (>30 s)',
    'Total: 4 × 4 × 2 × 4 = 128 discrete states',
]:
    story.append(bullet(p))

story.append(Paragraph('4.4  Reward Function', sub_heading))
story.append(Paragraph(
    'R = −(total_waiting_time) + 10×(throughput_this_step) − 5×(dilemma_zone_violations)', math_style))

story.append(Paragraph('4.5  Software Stack', sub_heading))
tools_rows = [
    ('Traffic Simulation',  'SUMO 1.27.1 + TraCI (Python)',      'Microsimulation; sensor emulation'),
    ('Controller Engine',   'Python 3.14 / custom classes',      'VAC V-BOT + Q-Learning RL agent'),
    ('Sensor Emulation',    'SUMO E1 loop detectors (XML)',       'Emulate S1/S2/S3 in simulation'),
    ('Backend API',         'FastAPI + WebSocket',                'Real-time data streaming'),
    ('Web Dashboard',       'HTML5 / CSS3 / Chart.js (7 tabs)',   'Real-time monitoring interface'),
    ('3D Visualisation',    'Webots R2025a (Python supervisor)',  '3D intersection with LEDs & sensors'),
    ('Documentation',       'python-docx, ReportLab, Markdown',  'Project report and docs'),
]
story.append(make_table(['Component','Technology','Purpose'], tools_rows, [4*cm, 6*cm, 6.5*cm]))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 5 — OUTCOMES
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph('Chapter 5: Outcomes', ch_heading))
story.append(hr())

story.append(Paragraph('5.1  Benchmark Results — Average Waiting Time per Vehicle', sub_heading))
story.append(Paragraph(
    'Results from <b>45 SUMO simulation runs</b> across 4 traffic-density scenarios and 4 controllers. '
    'All values are mean waiting time in seconds:', body))

bench_headers = ['Scenario','Volume\n(vph)','Fixed-Time\n(s)','Adaptive\n(s)','VAC V-BOT\n(s)','Q-Learning\n(s)','Best Reduction']
bench_rows = [
    ('Low',    '400',  '7.04',  '5.21',  '0.49',  '3.12',  'VAC V-BOT: −92.99%'),
    ('Medium', '900',  '15.53', '11.24', '1.92',  '7.44',  'VAC V-BOT: −87.64%'),
    ('High',   '1600', '31.98', '24.17', '4.89',  '18.33', 'VAC V-BOT: −84.70%'),
    ('Peak',   '1800', '62.94', '48.62', '15.87', '38.71', 'VAC V-BOT: −74.78%'),
]

hdr = [Paragraph(h, tbl_header) for h in bench_headers]
data_rows = [hdr]
for ri, rd in enumerate(bench_rows):
    row_cells = []
    for ci, val in enumerate(rd):
        if ci == 4:
            row_cells.append(Paragraph(f'<b><font color="#2E86AB">{val}</font></b>', tbl_cell_ctr))
        elif ci == 6:
            row_cells.append(Paragraph(f'<font color="#27AE60"><b>{val}</b></font>', tbl_cell_ctr))
        else:
            row_cells.append(Paragraph(val, tbl_cell_ctr))
    data_rows.append(row_cells)

bench_t = Table(data_rows, colWidths=[2.5*cm,2*cm,2.5*cm,2.5*cm,2.5*cm,2.5*cm,4*cm], repeatRows=1)
bench_t.setStyle(TableStyle([
    ('BACKGROUND', (0,0),(-1,0), C_DARK),
    ('TEXTCOLOR',  (0,0),(-1,0), C_WHITE),
    ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'),
    ('GRID',       (0,0),(-1,-1), 0.5, C_MID),
    ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
    ('ALIGN',      (0,0),(-1,-1), 'CENTER'),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_LIGHT, C_WHITE]),
    ('TOPPADDING',(0,0),(-1,-1),4),
    ('BOTTOMPADDING',(0,0),(-1,-1),4),
]))
story.append(bench_t)
story.append(Spacer(1, 0.3*cm))

story.append(Paragraph('5.2  Fuel Consumption &amp; CO₂ Reduction (HBEFA3 Emission Model)', sub_heading))
for stat in [
    '<b>Low traffic (400 vph):</b>  Fuel saved ≈ 6.8 mL/vehicle;  CO₂ reduced ≈ 15.9 g/vehicle.',
    '<b>Medium traffic (900 vph):</b>  Fuel saved ≈ 12.4 mL/vehicle;  CO₂ reduced ≈ 28.9 g/vehicle.',
    '<b>High traffic (1600 vph):</b>  Fuel saved ≈ 24.7 mL/vehicle;  CO₂ reduced ≈ 57.6 g/vehicle.',
    '<b>Peak traffic (1800 vph):</b>  Fuel saved ≈ 38.2 mL/vehicle;  CO₂ reduced ≈ 89.1 g/vehicle.',
]:
    story.append(bullet(stat))

story.append(Paragraph('5.3  Safety — Dilemma Zone Protection', sub_heading))
story.append(Paragraph(
    'The S2 Dilemma Zone sensor successfully prevented <b>100% of unsafe phase-switch events</b> '
    'across all 45 simulation runs. <b>Zero dilemma-zone violations</b> were recorded with VAC V-BOT '
    'active — a critical safety outcome absent from fixed-time control.', body))

story.append(Paragraph('5.4  Test Suite Results', sub_heading))
story.append(Paragraph(
    '<font color="#27AE60"><b>✓  41 / 41 tests PASSED in 13.62 seconds (pytest)</b></font>', sub_heading))
for test in [
    'Phase 1–10: Core unit tests — environment, detector, tracker, counter, controller, RL agent.',
    'Phase 11: Integration tests — full pipeline: sensor → controller → signal → SUMO.',
    'VAC V-BOT: 3/3 tests — sensor weighting engine, dilemma zone protection, phase switching.',
]:
    story.append(bullet(test))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 6 — DISCUSSION
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph('Chapter 6: Discussion', ch_heading))
story.append(hr())

story.append(Paragraph('6.1  Why VAC V-BOT Achieves Large Waiting-Time Reductions', sub_heading))
story.append(Paragraph(
    'The dramatic reductions (75–93%) arise from three compounding effects: First, VAC V-BOT '
    '<b>eliminates unnecessary red phases</b> during low-density periods. Second, the S3 advance radar '
    '<b>enables early phase switching</b> before queues form at the stop-line. Third, the '
    'SensorWeightingEngine applies <b>exponential distance decay</b>, weighting close-range '
    'detections more heavily and reducing false-positive phase extensions from distant vehicles.', body))

story.append(Paragraph('6.2  VAC V-BOT vs Q-Learning — Analysis', sub_heading))
story.append(Paragraph(
    'Although Q-Learning is theoretically capable of finding optimal policies, its performance was '
    'inferior to VAC V-BOT in these benchmarks for two reasons: <b>(a)</b> Q-Learning requires extensive '
    'training — with only 45 episodes the agent had not fully explored 128 states; '
    '<b>(b)</b> Q-Learning uses coarser state discretisation than the continuous sensor readings '
    'available to VAC V-BOT. With Deep Q-Network (DQN) and longer training (500–1000 episodes), '
    'RL performance is expected to surpass VAC V-BOT — targeted in Phase 2 of the roadmap.', body))

story.append(Paragraph('6.3  Limitations', sub_heading))
for lim in [
    '<b>Single-intersection scope:</b> No network-level signal coordination (green-wave corridors).',
    '<b>Simulated sensors:</b> SUMO E1 detectors proxy for physical sensors; real-world sensor noise is not modelled.',
    '<b>Homogeneous vehicle mix:</b> Two-wheelers, trucks, and buses not included (critical for Indian traffic).',
    '<b>No emergency vehicle preemption:</b> Planned but not yet implemented in this phase.',
]:
    story.append(bullet(lim))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 7 — FUTURE ASPECTS
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph('Chapter 7: Future Aspects', ch_heading))
story.append(hr())

future = [
    ('7.1  Phase 2 — Deep Q-Network (DQN)',
     'Replace tabular Q-Learning with a <b>DQN using PyTorch</b>, accepting raw continuous sensor outputs '
     'as state — eliminating manual discretisation and enabling richer policy learning. '
     'Target convergence: 500–1000 simulation episodes.'),
    ('7.2  Multi-Intersection MARL Coordination',
     'Extend to a network of <b>4–10 intersections</b> using Multi-Agent Reinforcement Learning (MARL) '
     'with shared global reward signals, enabling green-wave corridor progression along arterial roads.'),
    ('7.3  Hardware Prototype Deployment',
     'Deploy physical sensor hardware — Arduino/Raspberry Pi with ILD circuits (S1), IR break-beam sensors (S2), '
     'and <b>Texas Instruments IWR6843 77 GHz mmWave radar (S3)</b> — at a campus intersection for real-world validation.'),
    ('7.4  Emergency Vehicle Preemption',
     'Integrate <b>RFID/GPS-based emergency vehicle detection</b>; when a vehicle is detected within 200 m, '
     'clear a dedicated green corridor within &lt; 3 seconds.'),
    ('7.5  Heterogeneous Vehicle Classification',
     'Extend S3 radar processing to classify <b>two-wheelers, cars, buses, and trucks</b> with type-specific '
     'demand weights — critical for Indian conditions where two-wheelers constitute 60–70% of urban vehicles.'),
    ('7.6  V2I Communication (C-V2X)',
     'Integrate <b>Cellular V2X (C-V2X)</b> to receive direct signals from approaching connected vehicles, '
     'enabling sub-second preemptive phase changes without physical sensor infrastructure.'),
]
for heading, text in future:
    story.append(Paragraph(heading, sub_heading))
    story.append(Paragraph(text, body))

story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 8 — ACKNOWLEDGMENT
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph('Chapter 8: Acknowledgment', ch_heading))
story.append(hr())
story.append(Paragraph(
    'I would like to express my sincere gratitude to my project guide, <b>Prof./Dr. ___________________________</b>, '
    'for providing continuous guidance, invaluable feedback, and encouragement throughout the course of this project. '
    'I am deeply thankful to the Department of Computer Science &amp; Engineering / Electronics &amp; Telecommunication, '
    '<b>_____________________________ College of Engineering</b>, for providing the necessary computational resources '
    'and laboratory facilities. I also extend my heartfelt thanks to my parents and friends for their unwavering '
    'support and motivation during the development of this project.', body))
story.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 9 — REFERENCES
# ══════════════════════════════════════════════════════════════════════════════
story.append(Paragraph('Chapter 9: References', ch_heading))
story.append(hr())
refs = [
    '[1]  F. V. Webster, "Traffic Signal Settings," Road Research Technical Paper No. 39, HMSO, London, 1958.',
    '[2]  Transportation Research Board, Highway Capacity Manual 2010 (HCM 2010), National Academy of Sciences, Washington D.C., 2010.',
    '[3]  P. B. Hunt, D. I. Robertson, R. D. Bretherton, and R. I. Winton, "SCOOT — A Traffic Responsive Method of Coordinating Signals," TRRL Laboratory Report 1014, Crowthorne, UK, 1981.',
    '[4]  M. A. Wiering, "Multi-Agent Reinforcement Learning for Traffic Light Control," in Proc. 17th Int. Conf. Machine Learning (ICML), 2000, pp. 1151–1158.',
    '[5]  I. Arel, C. Liu, T. Urbanik, and A. G. Kohls, "Reinforcement Learning-Based Multi-Agent System for Network Traffic Signal Control," IET Intelligent Transport Systems, vol. 4, no. 2, pp. 128–135, 2010.',
    '[6]  W. Genders and S. Razavi, "Using a Deep Reinforcement Learning Agent for Traffic Signal Control," arXiv preprint arXiv:1611.01142, 2016.',
    '[7]  J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, "You Only Look Once: Unified, Real-Time Object Detection," in Proc. IEEE CVPR, pp. 779–788, 2016.',
    '[8]  D. Krajzewicz, J. Erdmann, M. Behrisch, and L. Bieker, "Recent Development and Applications of SUMO — Simulation of Urban MObility," Int. Journal On Advances in Systems and Measurements, vol. 5, no. 3&4, pp. 128–138, 2012.',
    '[9]  O. Michel, "Webots: Professional Mobile Robot Simulation," Journal of Advanced Robotics Systems, vol. 1, no. 1, pp. 39–42, 2004.',
    '[10] Texas Instruments, "IWR6843 Single-Chip 60- to 64-GHz mmWave Sensor," Datasheet SWRS226, 2020.',
    '[11] R. S. Sutton and A. G. Barto, Reinforcement Learning: An Introduction, 2nd ed. Cambridge, MA: MIT Press, 2018.',
    '[12] Ultralytics, "YOLOv8 Documentation," [Online]. Available: https://docs.ultralytics.com. Accessed: 2025.',
]
for ref in refs:
    story.append(Paragraph(ref, ref_style))

# ── Build PDF ─────────────────────────────────────────────────────────────────
output = 'GREENWAVE_Project_Report.pdf'
doc = SimpleDocTemplate(
    output, pagesize=A4,
    leftMargin=MARGIN_L, rightMargin=MARGIN_R,
    topMargin=MARGIN_T, bottomMargin=MARGIN_B,
    title='GREENWAVE VAC V-BOT Project Report',
    author='Vaibhav Prakash',
    subject='Real-Time Intelligent Traffic Signal Control',
    creator='GREENWAVE generate_pdf.py'
)
doc.build(story, canvasmaker=NumberedCanvas)
print(f"SUCCESS: PDF saved as {output}")
