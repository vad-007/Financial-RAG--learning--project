"""
generate_pdf.py
Creates a realistic fake earnings report PDF for NovaTech Corp.
Uses reportlab's Platypus layout engine for proper table and text rendering.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

OUTPUT_PATH = "/home/claude/financial_rag/data/novatech_earnings_report.pdf"


def build_styles():
    base = getSampleStyleSheet()
    custom = {
        "title":   ParagraphStyle("title",   parent=base["Title"],   fontSize=22, textColor=colors.HexColor("#1a1a2e"), spaceAfter=6),
        "subtitle":ParagraphStyle("subtitle",parent=base["Normal"],  fontSize=12, textColor=colors.HexColor("#4a4a6a"), spaceAfter=4, alignment=TA_CENTER),
        "h1":      ParagraphStyle("h1",      parent=base["Heading1"],fontSize=14, textColor=colors.HexColor("#1a1a2e"), spaceBefore=14, spaceAfter=6),
        "h2":      ParagraphStyle("h2",      parent=base["Heading2"],fontSize=12, textColor=colors.HexColor("#2e4057"), spaceBefore=10, spaceAfter=4),
        "body":    ParagraphStyle("body",    parent=base["Normal"],  fontSize=10, leading=14, spaceAfter=6),
        "note":    ParagraphStyle("note",    parent=base["Normal"],  fontSize=9,  textColor=colors.grey, leading=12, spaceAfter=4),
        "right":   ParagraphStyle("right",   parent=base["Normal"],  fontSize=10, alignment=TA_RIGHT),
    }
    return custom


def table_style(header_color=colors.HexColor("#2e4057")):
    return TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  header_color),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0),  10),
        ("ALIGN",       (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN",       (0, 0), (0, -1),  "LEFT"),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0,0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",(0, 0), (-1, -1), 8),
    ])


def generate():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    s = build_styles()
    story = []

    # ── Cover ──────────────────────────────────────────────────
    story += [
        Spacer(1, 0.5 * inch),
        Paragraph("NovaTech Corp.", s["title"]),
        Paragraph("Annual Earnings Report — Fiscal Year 2023", s["subtitle"]),
        Paragraph("For the twelve months ended December 31, 2023", s["subtitle"]),
        Spacer(1, 0.2 * inch),
        Paragraph("Ticker: NVT &nbsp;|&nbsp; Exchange: NASDAQ &nbsp;|&nbsp; ISIN: US6543210987", s["subtitle"]),
        Spacer(1, 1.5 * inch),
        Paragraph(
            "This document contains forward-looking statements. Actual results may differ "
            "materially from those projected. All figures in USD millions unless stated otherwise.",
            s["note"]
        ),
        PageBreak(),
    ]

    # ── Executive Summary ──────────────────────────────────────
    story.append(Paragraph("1. Executive Summary", s["h1"]))
    story.append(Paragraph(
        "NovaTech Corp. delivered strong financial performance in fiscal year 2023, "
        "with total revenue of <b>$4,820.5 million</b>, representing a <b>17.3% increase</b> "
        "year-over-year compared to $4,109.2 million in FY2022. Net income reached "
        "<b>$612.4 million</b>, up from $487.1 million in the prior year, driven by "
        "margin expansion in our Cloud Infrastructure and AI Solutions segments.",
        s["body"]
    ))
    story.append(Paragraph(
        "Earnings per share (diluted) came in at <b>$8.47</b> for FY2023 versus $6.73 in FY2022. "
        "The board of directors declared a quarterly dividend of <b>$0.42 per share</b> "
        "payable March 15, 2024. The company repurchased $310.0 million of common stock "
        "during the year under its share buyback program.",
        s["body"]
    ))
    story.append(Spacer(1, 0.1 * inch))

    # Key metrics table
    story.append(Paragraph("Key Performance Metrics", s["h2"]))
    kpi_data = [
        ["Metric",                   "FY2023",     "FY2022",     "YoY Change"],
        ["Total Revenue ($M)",       "$4,820.5",   "$4,109.2",   "+17.3%"],
        ["Gross Profit ($M)",        "$2,169.2",   "$1,768.0",   "+22.7%"],
        ["Gross Margin",             "45.0%",      "43.0%",      "+200 bps"],
        ["EBITDA ($M)",              "$963.5",     "$795.2",     "+21.2%"],
        ["EBITDA Margin",            "20.0%",      "19.3%",      "+70 bps"],
        ["Net Income ($M)",          "$612.4",     "$487.1",     "+25.7%"],
        ["Net Margin",               "12.7%",      "11.9%",      "+80 bps"],
        ["Diluted EPS ($)",          "$8.47",      "$6.73",      "+25.9%"],
        ["Free Cash Flow ($M)",      "$701.3",     "$553.8",     "+26.6%"],
        ["R&D Expense ($M)",         "$482.1",     "$390.4",     "+23.5%"],
    ]
    story.append(Table(kpi_data, colWidths=[2.4*inch, 1.2*inch, 1.2*inch, 1.2*inch], style=table_style()))
    story.append(Spacer(1, 0.15 * inch))

    # ── Revenue Breakdown ──────────────────────────────────────
    story.append(Paragraph("2. Revenue by Business Segment", s["h1"]))
    story.append(Paragraph(
        "NovaTech operates across four business segments. Cloud Infrastructure remained "
        "the largest contributor at 38.2% of total revenue, while AI Solutions was the "
        "fastest-growing segment with 41.5% year-over-year growth.",
        s["body"]
    ))
    seg_data = [
        ["Segment",             "FY2023 ($M)", "FY2022 ($M)", "YoY Growth", "% of Revenue"],
        ["Cloud Infrastructure","$1,841.5",   "$1,612.3",    "+14.2%",     "38.2%"],
        ["AI Solutions",        "$1,204.8",   "$851.9",      "+41.5%",     "25.0%"],
        ["Enterprise Software", "$1,098.7",   "$980.4",      "+12.1%",     "22.8%"],
        ["Professional Services","$675.5",    "$664.6",      "+1.6%",      "14.0%"],
        ["Total",               "$4,820.5",   "$4,109.2",    "+17.3%",     "100.0%"],
    ]
    t = Table(seg_data, colWidths=[1.9*inch, 1.1*inch, 1.1*inch, 1.0*inch, 1.0*inch], style=table_style())
    # Bold the totals row
    t.setStyle(TableStyle([
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8eaf6")),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.15 * inch))

    # ── Quarterly Revenue ──────────────────────────────────────
    story.append(Paragraph("3. Quarterly Revenue Breakdown — FY2023", s["h1"]))
    story.append(Paragraph(
        "Revenue growth accelerated through the year, with Q4 2023 representing the "
        "strongest quarter at $1,312.8 million, a 21.1% increase versus Q4 2022.",
        s["body"]
    ))
    q_data = [
        ["Quarter", "Revenue ($M)", "QoQ Change", "YoY Change"],
        ["Q1 2023", "$1,098.4",    "—",          "+12.1%"],
        ["Q2 2023", "$1,174.6",    "+6.9%",       "+15.4%"],
        ["Q3 2023", "$1,234.7",    "+5.1%",       "+18.7%"],
        ["Q4 2023", "$1,312.8",    "+6.3%",       "+21.1%"],
        ["Full Year","$4,820.5",   "—",           "+17.3%"],
    ]
    t2 = Table(q_data, colWidths=[1.5*inch, 1.5*inch, 1.3*inch, 1.3*inch], style=table_style())
    t2.setStyle(TableStyle([
        ("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8eaf6")),
    ]))
    story.append(t2)
    story.append(PageBreak())

    # ── Income Statement ───────────────────────────────────────
    story.append(Paragraph("4. Consolidated Income Statement", s["h1"]))
    inc_data = [
        ["Line Item",                        "FY2023 ($M)",  "FY2022 ($M)"],
        ["Revenue",                          "$4,820.5",     "$4,109.2"],
        ["Cost of Revenue",                  "($2,651.3)",   "($2,341.2)"],
        ["Gross Profit",                     "$2,169.2",     "$1,768.0"],
        ["Research & Development",           "($482.1)",     "($390.4)"],
        ["Sales & Marketing",                "($623.4)",     "($541.2)"],
        ["General & Administrative",         "($220.4)",     "($196.1)"],
        ["Total Operating Expenses",         "($1,325.9)",   "($1,127.7)"],
        ["Operating Income (EBIT)",          "$843.3",       "$640.3"],
        ["Interest Income",                  "$42.1",        "$28.4"],
        ["Interest Expense",                 "($51.8)",      "($47.2)"],
        ["Other Income / (Expense), net",    "$18.6",        "$12.5"],
        ["Pre-tax Income",                   "$852.2",       "$634.0"],
        ["Income Tax Expense (24%)",         "($204.5)",     "($152.2)"],  # Note: 24% effective rate
        ["Net Income",                       "$612.4",       "$487.1"],  # Note: ~28% growth... minor rounding
        # Note: small rounding delta intentional for realism
    ]
    story.append(Table(inc_data, colWidths=[3.2*inch, 1.4*inch, 1.4*inch], style=table_style()))
    story.append(Paragraph(
        "Note: Income tax reflects an effective rate of 24.0% (FY2022: 24.0%). "
        "Minor rounding differences may exist between individual line items and totals.",
        s["note"]
    ))
    story.append(Spacer(1, 0.15 * inch))

    # ── Balance Sheet ──────────────────────────────────────────
    story.append(Paragraph("5. Condensed Balance Sheet", s["h1"]))
    story.append(Paragraph("As of December 31, 2023 and December 31, 2022.", s["body"]))
    bs_data = [
        ["Assets",                            "Dec 31, 2023", "Dec 31, 2022"],
        ["Cash & Cash Equivalents",           "$1,204.5",     "$987.3"],
        ["Accounts Receivable, net",          "$842.1",       "$731.4"],
        ["Inventories",                       "$124.3",       "$108.7"],
        ["Other Current Assets",              "$213.6",       "$187.2"],
        ["Total Current Assets",             "$2,384.5",     "$2,014.6"],
        ["Property, Plant & Equipment, net",  "$1,102.3",     "$934.5"],
        ["Goodwill & Intangibles",            "$2,301.4",     "$2,100.8"],
        ["Other Long-term Assets",            "$412.7",       "$383.1"],
        ["Total Assets",                      "$6,200.9",     "$5,433.0"],
        ["",                                  "",             ""],
        ["Liabilities & Equity",             "Dec 31, 2023", "Dec 31, 2022"],
        ["Accounts Payable",                  "$412.3",       "$374.1"],
        ["Short-term Debt",                   "$200.0",       "$200.0"],
        ["Other Current Liabilities",         "$634.5",       "$551.2"],
        ["Total Current Liabilities",        "$1,246.8",     "$1,125.3"],
        ["Long-term Debt",                    "$1,400.0",     "$1,500.0"],
        ["Other Long-term Liabilities",       "$312.4",       "$287.6"],
        ["Total Liabilities",                "$2,959.2",     "$2,912.9"],
        ["Total Shareholders Equity",        "$3,241.7",     "$2,520.1"],
        ["Total Liabilities & Equity",       "$6,200.9",     "$5,433.0"],
    ]
    story.append(Table(bs_data, colWidths=[3.2*inch, 1.4*inch, 1.4*inch], style=table_style()))
    story.append(PageBreak())

    # ── Cash Flow ─────────────────────────────────────────────
    story.append(Paragraph("6. Cash Flow Statement", s["h1"]))
    cf_data = [
        ["Cash Flow Item",                         "FY2023 ($M)", "FY2022 ($M)"],
        ["Net Income",                             "$612.4",      "$487.1"],
        ["Depreciation & Amortization",            "$120.2",      "$154.9"],
        ["Stock-Based Compensation",               "$98.4",       "$85.3"],
        ["Changes in Working Capital",             "($30.5)",     "($42.7)"],
        ["Other Adjustments",                      "$12.1",       "$8.9"],
        ["Cash from Operations",                   "$812.6",      "$693.5"],
        ["Capital Expenditures",                   "($111.3)",    "($139.7)"],
        ["Acquisitions",                           "($0.0)",      "($215.0)"],
        ["Free Cash Flow",                         "$701.3",      "$553.8"],
        ["Proceeds from debt",                     "$0.0",        "$300.0"],
        ["Repayment of debt",                      "($100.0)",    "($0.0)"],
        ["Share repurchases",                      "($310.0)",    "($180.0)"],
        ["Dividends paid",                         "($121.6)",    "($108.4)"],
        ["Net Change in Cash",                     "$217.2",      "$265.4"],
    ]
    t3 = Table(cf_data, colWidths=[3.2*inch, 1.4*inch, 1.4*inch], style=table_style())
    t3.setStyle(TableStyle([
        ("FONTNAME",   (0, 7), (-1, 7),  "Helvetica-Bold"),
        ("BACKGROUND", (0, 7), (-1, 7),  colors.HexColor("#e8f5e9")),
        ("FONTNAME",   (0, 10), (-1, 10), "Helvetica-Bold"),
        ("BACKGROUND", (0, 10), (-1, 10), colors.HexColor("#e8f5e9")),
    ]))
    story.append(t3)
    story.append(Spacer(1, 0.15 * inch))

    # ── Debt Schedule ──────────────────────────────────────────
    story.append(Paragraph("7. Debt Schedule & Maturity Profile", s["h1"]))
    story.append(Paragraph(
        "As of December 31, 2023, NovaTech had total outstanding debt of $1,600.0 million "
        "across four instruments with a weighted average interest rate of 4.28%.",
        s["body"]
    ))
    debt_data = [
        ["Instrument",              "Principal ($M)", "Interest Rate", "Maturity Date",  "Type"],
        ["Senior Notes 2026",       "$400.0",         "3.75%",         "March 15, 2026", "Fixed"],
        ["Term Loan A",             "$500.0",         "SOFR + 1.50%",  "June 30, 2027",  "Floating"],
        ["Senior Notes 2029",       "$500.0",         "4.50%",         "Sept 1, 2029",   "Fixed"],
        ["Revolving Credit Facility","$200.0",        "SOFR + 1.25%",  "Dec 31, 2025",   "Floating"],
        ["Total",                   "$1,600.0",       "4.28% (wtd.avg.)","—",            "—"],
    ]
    t4 = Table(debt_data, colWidths=[1.7*inch, 1.2*inch, 1.2*inch, 1.3*inch, 0.8*inch], style=table_style())
    t4.setStyle(TableStyle([
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8eaf6")),
    ]))
    story.append(t4)
    story.append(Spacer(1, 0.15 * inch))

    # ── Outlook ────────────────────────────────────────────────
    story.append(Paragraph("8. FY2024 Guidance", s["h1"]))
    guide_data = [
        ["Metric",          "FY2024 Guidance",   "Midpoint"],
        ["Total Revenue",   "$5,400M – $5,600M", "$5,500M"],
        ["EBITDA Margin",   "20.5% – 21.5%",     "21.0%"],
        ["Diluted EPS",     "$9.20 – $9.60",     "$9.40"],
        ["Free Cash Flow",  "$800M – $880M",     "$840M"],
        ["CapEx",           "$130M – $150M",     "$140M"],
    ]
    story.append(Table(guide_data, colWidths=[2.0*inch, 2.0*inch, 1.5*inch], style=table_style()))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "Guidance assumes no material acquisitions, a USD/EUR rate of 1.08, and "
        "continued demand in Cloud Infrastructure and AI Solutions segments. "
        "The company expects AI Solutions to surpass $1.8 billion in revenue by Q4 2024.",
        s["body"]
    ))

    # ── Footer note ────────────────────────────────────────────
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        "NovaTech Corp. is a fictional company created for educational purposes. "
        "All numbers, names, and projections are entirely fabricated. "
        "This document is not an investment prospectus.",
        s["note"]
    ))

    doc.build(story)
    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate()
