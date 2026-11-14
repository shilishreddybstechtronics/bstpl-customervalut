"""
Main PDF Builder Script:
Compiles BSTPL_CustomerVault_Complete_Documentation.pdf
Using data from backend/docs_content.py
"""

import os
import sys
import re
import html
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

import docs_content

def clean_xml_for_reportlab(s):
    if not s:
        return ""
    def replace_tag(m):
        t = m.group(0)
        tl = t.lower()
        if tl in ('<br/>', '<br />', '<br>', '<b>', '</b>', '<i>', '</i>', '<code>', '</code>'):
            return '<br/>' if 'br' in tl else t
        return '&lt;' + t[1:-1] + '&gt;'
    s = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;)', '&amp;', s)
    return re.sub(r'<[^>]+>', replace_tag, s)


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 812, "BSTPL Customer Vault  |  Complete System Code & Execution Documentation Manual")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, 806, 559, 806)

        # Footer (all pages)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(559, 25, page_str)
        self.drawString(36, 25, "CONFIDENTIAL  -  BS TECHNOTRONICS PVT LTD  -  FOR INTERNAL & TECHNICAL AUDIT ONLY")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 35, 559, 35)
        self.restoreState()


def build_complete_pdf(filename="BSTPL_CustomerVault_Complete_Documentation.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'SecHeading1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SecHeading2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13.5,
        textColor=colors.HexColor("#0369a1"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e293b")
    )

    tbl_hdr = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.white)
    tbl_cell = ParagraphStyle('TC', fontName='Helvetica', fontSize=7.2, leading=9.5, textColor=colors.HexColor("#1e293b"))
    tbl_code = ParagraphStyle('TCode', fontName='Courier-Bold', fontSize=6.8, leading=8.8, textColor=colors.HexColor("#0f172a"))
    tbl_why = ParagraphStyle('TWhy', fontName='Helvetica', fontSize=7.2, leading=9.5, textColor=colors.HexColor("#0f766e"))
    tbl_exec = ParagraphStyle('TExec', fontName='Helvetica', fontSize=7.2, leading=9.5, textColor=colors.HexColor("#1d4ed8"))
    tbl_target = ParagraphStyle('TTarget', fontName='Helvetica-Bold', fontSize=7.2, leading=9.5, textColor=colors.HexColor("#1e293b"))

    story = []

    # ==========================================
    # COVER / HEADER CARD
    # ==========================================
    story.append(Paragraph("BS TECHNOTRONICS PVT LTD  &bull;  ENTERPRISE IOT & TELEMATICS PLATFORM", ParagraphStyle('SuperTitle', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor("#2563eb"), spaceAfter=3)))
    story.append(Paragraph("BSTPL Customer Vault System", title_style))
    story.append(Paragraph("<b>Complete Codebase &amp; Runtime Execution Documentation Manual</b><br/>Exhaustive Architectural Analysis Across All Backend (FastAPI, TiDB/SQLite, ORM, Dynamic Tables) and Frontend (Vanilla JS, SheetJS, HTML5 Modals, Real-time Grids) Modules.", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceBefore=0, spaceAfter=12))

    # Architecture Overview Callout
    overview_text = """
    <b>System Scope &amp; Architectural Blueprint:</b><br/>
    The <b>BSTPL Customer Vault</b> is an enterprise telematics inventory and customer asset vault engineered to process, validate,
    and monitor tens of thousands of IoT SIM cards and GPS tracking devices across telecommunications providers (Sensorise, Airtel, Vodafone, Jio).<br/>
    Unlike traditional monolithic database designs, the system incorporates a <b>Dual-Write Dynamic Isolation Architecture</b>:
    a unified master table (<code>sim_devices</code>) serves global search, auditing, and bulk operations, while <b>each customer organization is dynamically provisioned its own isolated physical SQL table</b> (e.g. <code>c7_sharon_logistics</code>) with automatic schema reflection and real-time synchronization.<br/>
    The frontend is built with high-performance responsive Vanilla JavaScript and native HTML5 dialogs, providing sub-millisecond client validations (including strict 15-digit IMEI and 19/20-digit ICCID integrity checks) and instant error self-healing consoles.<br/>
    This publication-grade document explains <b>why every core line was authored</b> and <b>how it executes at runtime</b> across both frontend and backend tiers.
    """
    story.append(Paragraph(overview_text, ParagraphStyle('Callout', fontName='Helvetica', fontSize=8, leading=11.5, textColor=colors.HexColor("#0f172a"), backColor=colors.HexColor("#f1f5f9"), borderPadding=8, spaceAfter=14)))

    # ==========================================
    # SECTION 1: MASTER REPOSITORY CATALOG
    # ==========================================
    story.append(Paragraph("1. Complete Repository Directory &amp; File Catalog", h1_style))
    story.append(Paragraph("Comprehensive inventory of all functional modules across backend services, client-side interfaces, and integration subsystems:", body_style))
    story.append(Spacer(1, 6))

    cat_widths = [110, 50, 55, 305]
    cat_data = [[
        Paragraph("File Path", tbl_hdr),
        Paragraph("Language", tbl_hdr),
        Paragraph("Size", tbl_hdr),
        Paragraph("Core Architectural Role &amp; System Purpose", tbl_hdr)
    ]]
    for fpath, lang, size, desc in docs_content.REPO_CATALOG:
        cat_data.append([
            Paragraph(f"<b>{clean_xml_for_reportlab(fpath)}</b>", tbl_target),
            Paragraph(clean_xml_for_reportlab(lang), tbl_cell),
            Paragraph(clean_xml_for_reportlab(size), tbl_cell),
            Paragraph(clean_xml_for_reportlab(desc), tbl_cell)
        ])
    t_cat = Table(cat_data, colWidths=cat_widths, repeatRows=1)
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1e3a8a")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_cat)
    story.append(Spacer(1, 14))

    # ==========================================
    # HELPER TO RENDER CODE TABLES
    # ==========================================
    def render_code_table(rows):
        col_widths = [65, 155, 150, 150]
        tbl_data = [[
            Paragraph("Line / Target", tbl_hdr),
            Paragraph("Exact Code / Construct", tbl_hdr),
            Paragraph("Why Written (Architectural Purpose)", tbl_hdr),
            Paragraph("How It Executes (Runtime Mechanics)", tbl_hdr)
        ]]
        for target, code, why, how in rows:
            tbl_data.append([
                Paragraph(clean_xml_for_reportlab(target), tbl_target),
                Paragraph(clean_xml_for_reportlab(code), tbl_code),
                Paragraph(clean_xml_for_reportlab(why), tbl_why),
                Paragraph(clean_xml_for_reportlab(how), tbl_exec)
            ])
        tbl = Table(tbl_data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1e3a8a")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        return tbl

    # ==========================================
    # SECTION 2: BACKEND CORE MODULES
    # ==========================================
    story.append(PageBreak())
    story.append(Paragraph("2. Backend Core Modules — Code &amp; Runtime Execution", h1_style))
    story.append(Paragraph("Detailed line-by-line and statement block breakdown of server entrypoints, database connection resiliency, ORM data models, dynamic customer table engine, and RESTful routing services.", body_style))
    story.append(Spacer(1, 8))

    # 2.1 Server Entry (app.py)
    story.append(Paragraph("2.1 Server Entry Point &amp; Port Resolution (<code>backend/app.py</code>)", h2_style))
    story.append(render_code_table(docs_content.BACKEND_APP_PY))
    story.append(Spacer(1, 10))

    # 2.2 Database Layer (database.py)
    story.append(Paragraph("2.2 Database Layer &amp; Connection Resilience (<code>backend/database.py</code>)", h2_style))
    story.append(render_code_table(docs_content.BACKEND_DATABASE_PY))
    story.append(Spacer(1, 10))

    # 2.3 ORM Models (models.py)
    story.append(Paragraph("2.3 Relational ORM Entity Models (<code>backend/models.py</code>)", h2_style))
    story.append(render_code_table(docs_content.BACKEND_MODELS_PY))
    story.append(Spacer(1, 10))

    # 2.4 Dynamic Customer Tables (customer_tables.py)
    story.append(PageBreak())
    story.append(Paragraph("2.4 Dynamic Customer Isolation Engine (<code>backend/customer_tables.py</code>)", h2_style))
    story.append(render_code_table(docs_content.BACKEND_CUSTOMER_TABLES_PY))
    story.append(Spacer(1, 10))

    # 2.5 Customer Routes (routes_customers.py)
    story.append(Paragraph("2.5 Customer Lifecycle &amp; Safe Deletion Router (<code>backend/routes_customers.py</code>)", h2_style))
    story.append(render_code_table(docs_content.BACKEND_ROUTES_CUSTOMERS_PY))
    story.append(Spacer(1, 10))

    # 2.6 Data Ingestion Routes (routes_data.py)
    story.append(Paragraph("2.6 Data Ingestion, Hardware Length Validation &amp; Query Engine (<code>backend/routes_data.py</code>)", h2_style))
    story.append(render_code_table(docs_content.BACKEND_ROUTES_DATA_PY))
    story.append(Spacer(1, 14))

    # ==========================================
    # SECTION 3: FRONTEND CLIENT ARCHITECTURE
    # ==========================================
    story.append(PageBreak())
    story.append(Paragraph("3. Frontend Architecture &amp; Client-Side Execution", h1_style))
    story.append(Paragraph("In-depth breakdown of the client-side JavaScript execution layer, DOM event listeners, modal managers, SheetJS parser, exact-length verification, and interactive consoles.", body_style))
    story.append(Spacer(1, 8))

    # 3.1 Core Utilities (cv-popup.js, cart-modal.js, app.js)
    story.append(Paragraph("3.1 Universal Client Core (<code>cv-popup.js</code>, <code>cart-modal.js</code>, <code>app.js</code>)", h2_style))
    story.append(render_code_table(docs_content.FRONTEND_CORE_JS))
    story.append(Spacer(1, 10))

    # 3.2 Authentication UI (login.html)
    story.append(Paragraph("3.2 Authentication Gateway (<code>frontend/login.html</code>)", h2_style))
    story.append(render_code_table(docs_content.FRONTEND_LOGIN_HTML))
    story.append(Spacer(1, 10))

    # 3.3 Dashboard (dashboard.html / home.html)
    story.append(Paragraph("3.3 Executive Telemetry Dashboard (<code>frontend/dashboard.html</code>)", h2_style))
    story.append(render_code_table(docs_content.FRONTEND_DASHBOARD_HTML))
    story.append(Spacer(1, 10))

    # 3.4 Inventory Grid (inventory.html)
    story.append(PageBreak())
    story.append(Paragraph("3.4 Unified Device Inventory Grid &amp; Expiry Summary (<code>frontend/inventory.html</code>)", h2_style))
    story.append(render_code_table(docs_content.FRONTEND_INVENTORY_HTML))
    story.append(Spacer(1, 10))

    # 3.5 Bulk SIM Ingestion (sim-upload.html)
    story.append(Paragraph("3.5 Bulk Ingestion &amp; Exact-Length Validation Pipeline (<code>frontend/sim-upload.html</code>)", h2_style))
    story.append(render_code_table(docs_content.FRONTEND_SIM_UPLOAD_HTML))
    story.append(Spacer(1, 10))

    # 3.6 Error Quarantine Console (errors.html)
    story.append(Paragraph("3.6 Errored Entries Resolution Console (<code>frontend/errors.html</code>)", h2_style))
    story.append(render_code_table(docs_content.FRONTEND_ERRORS_HTML))
    story.append(Spacer(1, 10))

    # 3.7 Sensorise Fetch Console (fetch-data.html)
    story.append(PageBreak())
    story.append(Paragraph("3.7 Sensorise IoT Cloud Fetch &amp; Sync Console (<code>frontend/fetch-data.html</code>)", h2_style))
    story.append(render_code_table(docs_content.FRONTEND_FETCH_DATA_HTML))
    story.append(Spacer(1, 10))

    # 3.8 Alerts Engine (alerts.html)
    story.append(Paragraph("3.8 Warranty &amp; SIM Expiry Alerts Engine (<code>frontend/alerts.html</code>)", h2_style))
    story.append(render_code_table(docs_content.FRONTEND_ALERTS_HTML))
    story.append(Spacer(1, 10))

    # 3.9 Edit & Delete Console (edit-delete.html)
    story.append(Paragraph("3.9 Batch Operations &amp; Customer Reassignment (<code>frontend/edit-delete.html</code>)", h2_style))
    story.append(render_code_table(docs_content.FRONTEND_EDIT_DELETE_HTML))
    story.append(Spacer(1, 10))

    # 3.10 Settings Console (settings.html)
    story.append(Paragraph("3.10 System Settings &amp; Custom Column Manager (<code>frontend/settings.html</code>)", h2_style))
    story.append(render_code_table(docs_content.FRONTEND_SETTINGS_HTML))
    story.append(Spacer(1, 14))

    # ==========================================
    # SECTION 4: END-TO-END EXECUTION TRACES
    # ==========================================
    story.append(PageBreak())
    story.append(Paragraph("4. End-to-End System Execution Lifecycle Traces", h1_style))
    story.append(Paragraph("Comprehensive walkthroughs showing how requests propagate across Browser DOM, HTTP Network, FastAPI Middleware, Database Transactions, and TiDB/SQLite dynamic customer tables.", body_style))
    story.append(Spacer(1, 8))

    trace_widths = [140, 380]
    for trace in docs_content.LIFECYCLE_TRACES:
        story.append(Paragraph(clean_xml_for_reportlab(trace["title"]), h2_style))
        t_data = [[
            Paragraph("Lifecycle Phase", tbl_hdr),
            Paragraph("System Action, Memory State, &amp; Database Transaction", tbl_hdr)
        ]]
        for step_name, step_desc in trace["steps"]:
            t_data.append([
                Paragraph(f"<b>{clean_xml_for_reportlab(step_name)}</b>", tbl_target),
                Paragraph(clean_xml_for_reportlab(step_desc), tbl_cell)
            ])
        t_tbl = Table(t_data, colWidths=trace_widths, repeatRows=1)
        t_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1e3a8a")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(t_tbl)
        story.append(Spacer(1, 10))

    # Build the PDF using our NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated complete documentation PDF: {filename}")

if __name__ == "__main__":
    out_pdf = "BSTPL_CustomerVault_Complete_Documentation.pdf"
    if len(sys.argv) > 1:
        out_pdf = sys.argv[1]
    build_complete_pdf(out_pdf)
