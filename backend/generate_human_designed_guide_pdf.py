"""
Publication-Grade Engineering Guide PDF Generator:
BSTPL Human-Designed Architecture & Code Craftsmanship Manual
Contrasts 'Robotic/Naive Implementation' vs 'Human-Designed Enterprise Architecture'
across both Backend and Frontend tiers.
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
            self.drawString(36, 812, "BSTPL Customer Vault  |  Human-Designed Software Engineering & Code Craftsmanship")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, 806, 559, 806)

        # Footer (all pages)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(559, 25, page_str)
        self.drawString(36, 25, "CONFIDENTIAL  -  BS TECHNOTRONICS PVT LTD  -  ENTERPRISE ARCHITECTURE STANDARD")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 35, 559, 35)
        self.restoreState()


def build_human_designed_pdf(filename="BSTPL_Human_Designed_Architecture_and_Code_Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )

    section_style = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1e3a8a"),
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )

    sub_style = ParagraphStyle(
        'SubTitle',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#0369a1"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )

    tbl_hdr = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=7.2, leading=9.2, textColor=colors.white)
    tbl_cell = ParagraphStyle('TC', fontName='Helvetica', fontSize=7, leading=9, textColor=colors.HexColor("#1e293b"))
    tbl_bad = ParagraphStyle('TBad', fontName='Helvetica', fontSize=6.8, leading=8.8, textColor=colors.HexColor("#991b1b"))
    tbl_good = ParagraphStyle('TGood', fontName='Helvetica', fontSize=6.8, leading=8.8, textColor=colors.HexColor("#065f46"))
    tbl_code = ParagraphStyle('TCode', fontName='Courier-Bold', fontSize=6.5, leading=8.5, textColor=colors.HexColor("#0f172a"))
    tbl_target = ParagraphStyle('TTarget', fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=colors.HexColor("#1e293b"))

    def render_contrast_table(rows):
        col_widths = [110, 205, 205]
        data = [[
            Paragraph("Engineering Domain", tbl_hdr),
            Paragraph("The Naive / Robotic Way (Problems &amp; Flaws)", tbl_hdr),
            Paragraph("The Human-Designed Way (Craftsmanship &amp; Resilience)", tbl_hdr)
        ]]
        for domain, bad, good in rows:
            data.append([
                Paragraph(clean_xml_for_reportlab(domain), tbl_target),
                Paragraph(clean_xml_for_reportlab(bad), tbl_bad),
                Paragraph(clean_xml_for_reportlab(good), tbl_good)
            ])
        tbl = Table(data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1e3a8a")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        return tbl

    def render_table(headers, rows, col_widths):
        data = [[Paragraph(clean_xml_for_reportlab(h), tbl_hdr) for h in headers]]
        for row in rows:
            formatted_row = []
            for idx, cell in enumerate(row):
                if idx == 0:
                    formatted_row.append(Paragraph(clean_xml_for_reportlab(cell), tbl_target))
                else:
                    formatted_row.append(Paragraph(clean_xml_for_reportlab(cell), tbl_cell))
            data.append(formatted_row)
        tbl = Table(data, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1e3a8a")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        return tbl

    story = []

    # ==========================================
    # COVER CARD
    # ==========================================
    story.append(Paragraph("BS TECHNOTRONICS PVT LTD  &bull;  SOFTWARE CRAFTSMANSHIP STANDARDS", ParagraphStyle('Super', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.HexColor("#2563eb"), spaceAfter=2)))
    story.append(Paragraph("Human-Designed Architecture &amp; Code Craftsmanship Manual", title_style))
    story.append(Paragraph("<b>How Senior Engineers Thoughtfully Structure, Comment, and Build Full-Stack Software</b><br/>Contrasting Robotic / Monolithic Boilerplate against Human-Centric Code Architecture across Backend and Frontend.", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563eb"), spaceBefore=0, spaceAfter=10))

    # ==========================================
    # SECTION 1: THE CORE PHILOSOPHY
    # ==========================================
    story.append(Paragraph("1. The Philosophy of Human-Designed Code", section_style))
    p1_text = """
    Software written in a 'human-designed way' is fundamentally distinct from code generated mechanically or dumped into monolithic scripts.
    Human software craftsmanship is guided by four core pillars:
    <br/><br/>
    <b>1. Empathy for the Operator &amp; Developer:</b> Error messages are not generic HTTP 400s; they tell the human operator exactly what went wrong (e.g. <i>'IMEI too short: 14 digits (expected exact 15)'</i>) and provide immediate interactive controls to rectify the issue without discarding their work.
    <br/>
    <b>2. Defensive Intent &amp; Edge-Case Awareness:</b> A human engineer knows that databases fail, networks disconnect, and circular renames occur. The code anticipates these failure modes in advance (e.g. two-phase temporary name swapping, zero-downtime SQLite fallback).
    <br/>
    <b>3. Clean Cognitive Chunking:</b> Instead of 1,000-line monolithic files with scattered logic, human code is organized into logical, self-contained sections separated by clear visual dividers, with explanatory headers describing <i>why</i> decisions were made.
    <br/>
    <b>4. Separation of Concerns without Bloat:</b> Zero heavy, fragile build steps. Pure Vanilla JS and native HTML5 dialogs on the client; clean FastAPI dependencies and SQLAlchemy sessions on the server.
    """
    story.append(Paragraph(p1_text, body_style))
    story.append(Spacer(1, 8))

    # ==========================================
    # SECTION 2: BACKEND CRAFTSMANSHIP
    # ==========================================
    story.append(Paragraph("2. Backend Craftsmanship: The Human vs. The Robotic Approach", section_style))
    story.append(Paragraph("Comparative architectural analysis of core backend implementations across routing, transactions, and data isolation:", body_style))
    story.append(Spacer(1, 4))

    backend_contrasts = [
        (
            "FastAPI Route Hierarchy &amp; Shadowing",
            "Declaring <code>@router.get('/{cid}')</code> before <code>@router.get('/bin')</code>.<br/>FastAPI evaluates routes top-down. It attempts to parse 'bin' as an integer ID, throwing an unhandled <b>422 Unprocessable Content</b> error.",
            "Understanding framework AST route dispatch.<br/>Placing static subpaths (<code>/bin</code>) physically above wildcard parameterized routes (<code>/{cid}</code>) with explicit docstrings warning future developers not to alter the order."
        ),
        (
            "Batch Customer Renaming &amp; Swaps",
            "Executing a single SQL UPDATE loop: <code>for c in renames: c.name = new_name</code>.<br/>If an operator performs a circular swap (Customer A &rarr; B and Customer B &rarr; A), the very first update trips the database UNIQUE constraint and crashes the entire transaction.",
            "Engineering a two-phase atomic rename pipeline.<br/>Phase 1 temporarily sets placeholder identifiers (<code>__renaming_{cid}</code>) and flushes the session. Phase 2 applies final names and commits. Swaps execute flawlessly with zero collisions."
        ),
        (
            "Database Resilience &amp; Connection Dropping",
            "Connecting with a single static connection string.<br/>When TiDB Cloud undergoes maintenance, SSL renegotiation, or temporary internet interruption, the server crashes with unhandled OperationalErrors, taking the platform offline.",
            "Implementing zero-downtime resilience with pre-ping validation.<br/>Attempts secure TLS connection with system root CA. If unreachable, catches the exception and seamlessly falls back to a high-concurrency local SQLite engine with PRAGMA WAL mode."
        ),
        (
            "High-Volume Device Mutation Performance",
            "Iterating ORM models in Python: <code>for dev in devices: dev.customer_id = target_id</code>.<br/>Loads 5,000 Python model objects into RAM, creating massive garbage collection spikes and taking seconds to commit.",
            "Executing direct database engine updates with <code>synchronize_session=False</code>.<br/>Bypasses in-memory ORM hydration, executing a single high-speed SQL UPDATE directly in the database engine with O(1) memory overhead."
        ),
        (
            "Customer Table Isolation Architecture",
            "Dumping every customer into one giant table with complex filtering, causing query slowdowns and index bloat.",
            "Dual-Write Dynamic Table Engine.<br/>Maintains a master table for unified searching, while automatically creating and synchronizing dedicated SQL tables (<code>c&lt;id&gt;_&lt;name&gt;</code>) per customer, with automated dynamic column reflection."
        )
    ]
    story.append(render_contrast_table(backend_contrasts))
    story.append(Spacer(1, 10))

    # ==========================================
    # SECTION 3: FRONTEND CRAFTSMANSHIP
    # ==========================================
    story.append(PageBreak())
    story.append(Paragraph("3. Frontend Craftsmanship: The Human vs. The Robotic Approach", section_style))
    story.append(Paragraph("How client-side architecture was built to prioritize human operator ergonomics, live validation, and zero-loss workflows:", body_style))
    story.append(Spacer(1, 4))

    frontend_contrasts = [
        (
            "Handling Corrupted Upload Data",
            "Showing a generic alert: <i>'Upload failed: Invalid row'</i>, aborting the whole 5,000-row batch and forcing the operator to manually inspect Excel files outside the browser.",
            "Interactive Self-Healing Modal (<code>#dlgImproperLengthAlert</code>).<br/>Intercepts length deviations, calculates valid vs flawed rows, and presents Option 1 (Quarantine to Errored Entries) and Option 2 (Inline Rectification with live green badge validation)."
        ),
        (
            "Telematics Length Verification",
            "Blindly trusting spreadsheet inputs or validating only on the backend after large file transmission.",
            "Client-Side Pre-Validation Gate (<code>findImproperLengthRows</code>).<br/>Inspects parsed memory buffer using SheetJS: IMEI must be strictly 15 digits; ICCID must be 19 or 20 digits. Catches errors sub-millisecond before hitting the network."
        ),
        (
            "Inventory Expiry Display Ergonomics",
            "Showing two clumsy, conflicting tables on the same page, cluttering the screen and confusing operators.",
            "Clean Single-View Toggle Switch.<br/>Provides a polished pill switch (Cards View vs Table View) that renders only one clear view at a time, keeping the workspace uncluttered and executive-ready."
        ),
        (
            "Dialog & Modal Management",
            "Ad-hoc <code>div.style.display='block'</code> hacks scattered across files, resulting in un-dismissible modals and focus trapping bugs.",
            "Centralized Modal Core (<code>cv-popup.js</code>).<br/>Built on native HTML5 <code>&lt;dialog&gt;</code> API with <code>showModal()</code>, automatic backdrop blur, Escape key dismissal, outside-click closing, and animated toast notifications."
        ),
        (
            "Cross-Tab State Synchronization",
            "Requiring manual page refreshes to see updated cart staging counts across multiple browser tabs.",
            "Event-Driven State Sync (<code>cart-modal.js</code>).<br/>Binds to browser <code>localStorage</code> storage events, instantly updating cart badge counts across all active browser tabs in real-time."
        )
    ]
    story.append(render_contrast_table(frontend_contrasts))
    story.append(Spacer(1, 10))

    # ==========================================
    # SECTION 4: CODE EXAMPLE: HUMAN-CRAFTED ROUTER
    # ==========================================
    story.append(Paragraph("4. Real Code Artifact: The Human-Crafted Customer Router", section_style))
    story.append(Paragraph("Below is an architectural excerpt from <code>backend/routes_customers.py</code> demonstrating human engineering craftsmanship:", body_style))
    story.append(Spacer(1, 4))

    code_sample = """
# Clear Section Banners &amp; Intent-Revealing Declarations
# ==============================================================================
# SECTION 2: CUSTOMER QUERIES &amp; RETRIEVAL ENDPOINTS
# ==============================================================================

# NOTE: /bin MUST remain physically registered ABOVE /{cid} to prevent route collision!
@router.get("/bin", summary="List soft-deleted customers in recycling bin")
def list_deleted_customers(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    # Clear SQL outer join query aggregating device counts for soft-deleted customers
    deleted_records = (
        db.query(Customer, func.count(Device.id))
        .outerjoin(Device, Device.customer_id == Customer.id)
        .filter(Customer.deleted_at.isnot(None))
        .group_by(Customer.id)
        .order_by(Customer.deleted_at.desc())
        .all()
    )
    return [{"id": c.id, "name": c.name, "devices": count, "deleted_at": c.deleted_at} 
            for c, count in deleted_records]

# Two-Phase Atomic Swap Pattern (Preventing SQL Unique Collisions)
# Phase 1: Set temporary placeholders so circular swaps (A -> B and B -> A) succeed
for customer, _ in pending_changes:
    customer.name = f"__renaming_{customer.id}"
db.flush()

# Phase 2: Commit final sanitized names
for customer, final_name in pending_changes:
    customer.name = final_name
db.commit()
"""
    story.append(Paragraph(clean_xml_for_reportlab(code_sample), ParagraphStyle('CodeBox', fontName='Courier-Bold', fontSize=6.5, leading=8.5, textColor=colors.HexColor("#0f172a"), backColor=colors.HexColor("#f1f5f9"), borderPadding=6, spaceAfter=8)))

    # ==========================================
    # SECTION 5: HUMAN DESIGN CHECKLIST
    # ==========================================
    story.append(Paragraph("5. The Senior Engineer's Human Craftsmanship Checklist", section_style))
    checklist_data = [
        ("Engineering Attribute", "Standard for Backend Code", "Standard for Frontend Code"),
        ("Naming &amp; Readability", "Use intent-revealing names (e.g. affected_devices_count, not n).", "Descriptive element IDs and functions (e.g. promptImproperLengthModal, not dlg)."),
        ("Error Communication", "Return actionable error messages explaining the violation.", "Show visual error cards with color-coded badges and inline rectification tools."),
        ("Architecture Isolation", "Group into Helper Guards, Read Endpoints, Mutations, and Purge.", "Decouple into Markup (HTML), Presentation (CSS), and Component Logic (JS)."),
        ("Performance Mindset", "Bypass in-memory ORM overhead with synchronize_session=False.", "Debounce search inputs (300ms) and paginate data grids to avoid DOM thrashing."),
        ("Resilience &amp; Fallback", "Test connection health with SELECT 1 and fail over to SQLite WAL.", "Handle network failures with animated toast alerts and auto-login redirects on 401.")
    ]
    story.append(render_table(
        ["Engineering Attribute", "Standard for Backend Code", "Standard for Frontend Code"],
        checklist_data[1:],
        [105, 205, 210]
    ))
    story.append(Spacer(1, 10))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated human-designed craftsmanship guide PDF: {filename}")

if __name__ == "__main__":
    out_pdf = "BSTPL_Human_Designed_Architecture_and_Code_Guide.pdf"
    if len(sys.argv) > 1:
        out_pdf = sys.argv[1]
    build_human_designed_pdf(out_pdf)
