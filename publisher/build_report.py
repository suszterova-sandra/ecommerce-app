"""
Build publisher/vec_business_report.json: a GoodData document (v2) over the VEC workspace visualizations,
styled to go with publisher/vec_theme.json (VEC blue #1662F4, navy #003264, Manrope).

    python3 publisher/build_report.py

Layout notes
- No small spacer elements: an empty text spacer renders with a minimum height, a scrollbar and an
  "Add text here" placeholder, so cards sit directly in their rows and rely on the renderer's own gaps.
  Spacers are only used for large empty areas (cover, chapter and closing pages) and the accent rules.
- KPI tiles and chart cards use a very light grey (CARD); the page stays white.
- Headings use the paragraph text styles (largeText / normalText) with bold markdown: the heading styles
  (h1-h6) rendered as a tiny dash in the document editor.
- Visualizations render without their own titles, so each card carries a label taken from the visualization
  YAML title in analytics/visualisations/.
- The "What stands out" panels repeat facts from the VEC dashboard widget descriptions; review them when the
  data or the report period changes.
"""
import itertools
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLUE, NAVY, WHITE = "#1662F4", "#003264", "#FFFFFF"
CARD = "#F4F6F9"  # very light grey behind KPI tiles and charts
GREEN_ALT, PANEL_TEXT, INK = "#7FFA88", "#C9D9FC", "#161616"
DATE = "work_date"
_spacer = itertools.count(1)
_page = "page"


def viz_titles():
    titles = {}
    for f in (ROOT / "analytics" / "visualisations").glob("*.yaml"):
        src = f.read_text()
        vid = re.search(r"^id:\s*(\S+)", src, re.M).group(1)
        titles[vid] = re.search(r"^title:\s*(.+)$", src, re.M).group(1).strip().strip('"')
    return titles


TITLES = viz_titles()


# ---------------------------------------------------------------- primitives

def spacer(proportion=None, style=None):
    node = {"type": "row", "children": [
        {"type": "text", "id": f"{_page}_sp{next(_spacer)}", "decorative": True}]}
    if proportion is not None:
        node["proportion"] = proportion
    if style:
        node["style"] = style
    return node


def text(tid, markdown, text_style="normalText", proportion=None, **style):
    node = {"type": "text", "id": tid, "markdown": markdown, "style": {"text_style": text_style, **style}}
    if proportion is not None:
        node["proportion"] = proportion
    return node


def heading(tid, label, text_style="largeText", proportion=None, as_title=False, **style):
    node = text(tid, f"**{label}**", text_style, proportion, **style)
    if as_title:
        node["type"] = "title"
    return node


def rule(proportion, ratio=None):
    """Blue accent line: the theme's accent_bar image, left-aligned. (A coloured row needs spacer text boxes,
    which show 'Add text here' and white artefacts next to the line.)"""
    return {"type": "image", "id": f"{_page}_rule{next(_spacer)}", "proportion": proportion, "decorative": True,
            "source": "{theme.assets.images.accent_bar}",
            "style": {"fit": "contain", "horizontal_align": "left", "vertical_align": "center"}}


def blank(proportion):
    """Empty area that lets the page background show. Holds a non-breaking space so the editor does not show
    the 'Add text here' placeholder of an empty text box."""
    return {"type": "text", "id": f"{_page}_blank{next(_spacer)}", "proportion": proportion, "decorative": True,
            "markdown": "\u00a0", "style": {"text_style": "smallText"}}


def card(children, background=CARD, proportion=None):
    """Column with a background. No inner spacers: empty text spacers render with a minimum height and scroll."""
    node = {"type": "column", "style": {"background_color": background}, "children": children}
    if proportion is not None:
        node["proportion"] = proportion
    return node


def plain_row(children, proportion):
    return {"type": "row", "proportion": proportion, "children": children}


def viz(vid, visualization):
    return {"type": "visualization", "id": vid, "visualization": visualization, "date": DATE}


# ---------------------------------------------------------------- building blocks

def kpi_tile(visualization):
    return card([
        heading(f"{_page}_{visualization}_lbl", TITLES[visualization].upper(), "smallText", 1,
                text_color=BLUE, horizontal_align="center", vertical_align="bottom"),
        {"type": "column", "proportion": 2.2, "children": [viz(f"{_page}_{visualization}", visualization)]},
    ])


def kpi_row(kpis, proportion=2.6):
    return plain_row([kpi_tile(k) for k in kpis], proportion)


def chart_card(vid, visualization, proportion=None):
    return card([
        heading(f"{vid}_lbl", TITLES[visualization], "normalText", 1, vertical_align="center"),
        {"type": "column", "proportion": 8, "children": [viz(vid, visualization)]},
    ], proportion=proportion)


def insight(body, proportion=1.3, label="What stands out"):
    return card([
        heading(f"{_page}_ih", label, "normalText", 1, text_color=WHITE, vertical_align="center"),
        text(f"{_page}_ib", body, "smallText", 5.5, text_color=PANEL_TEXT),
    ], background=NAVY, proportion=proportion)


def footer(chapter):
    return {"type": "row", "proportion": 0.6, "children": [
        {"type": "image", "id": f"{_page}_logo", "decorative": True, "source": "{theme.logo}",
         "style": {"fit": "contain", "horizontal_align": "left", "vertical_align": "bottom"}},
        {"type": "text", "id": f"{_page}_section", "proportion": 6, "decorative": True, "markdown": chapter,
         "style": {"text_style": "smallText", "horizontal_align": "center", "vertical_align": "bottom"}},
        {"type": "text", "id": f"{_page}_pageno", "decorative": True,
         "markdown": "{currentPageNumber} / {totalPages}",
         "style": {"text_style": "smallText", "horizontal_align": "right", "vertical_align": "bottom"}}]}


def content_page(page_id, chapter, kicker, title, lead, body_rows):
    """Header (kicker, title, lead, accent rule), body rows separated by gaps, footer."""
    global _page
    _page = page_id
    children = [
        {"type": "column", "proportion": 2.4, "children": [
            text(f"{page_id}_kicker", kicker, "smallText", 0.8, text_color=BLUE, vertical_align="bottom"),
            heading(f"{page_id}_title", title, "largeText", 1.3, as_title=True, vertical_align="center"),
            text(f"{page_id}_lead", lead, "normalText", 1, vertical_align="top")]},
        rule(0.05),
        *body_rows(),
        footer(chapter),
    ]
    return {"id": page_id, "kind": "content", "layout": {"type": "column", "children": children}}


def kpi_page(page_id, chapter, kicker, title, lead, kpis, chart, chart_vis, body):
    return content_page(page_id, chapter, kicker, title, lead, lambda: [
        kpi_row(kpis),
        plain_row([chart_card(chart, chart_vis, proportion=2.7), insight(body)], 5.4)])


def two_chart_page(page_id, chapter, kicker, title, lead, left, right, body, left_weight=1.0):
    return content_page(page_id, chapter, kicker, title, lead, lambda: [
        plain_row([chart_card(left[0], left[1], proportion=left_weight),
                   chart_card(right[0], right[1]),
                   insight(body, proportion=0.75)], 8)])


def chapter_page(page_id, number, name, description, contents):
    global _page
    _page = page_id
    return {"id": page_id, "kind": "section",
            "style": {"background_color": NAVY, "background_image": "{theme.assets.images.cover_bg}"},
            "layout": {"type": "row", "children": [
                blank(1.4),
                card([
                    heading(f"{page_id}_num", number, "largeText", 3.5, text_color=GREEN_ALT,
                            vertical_align="bottom"),
                    heading(f"{page_id}_title", name, "largeText", 1.6, as_title=True,
                            text_color=WHITE, vertical_align="center"),
                    rule(0.06),
                    text(f"{page_id}_desc", f"{description}\n\n**In this chapter:** {contents}",
                         "normalText", 4, text_color=PANEL_TEXT, vertical_align="top"),
                ], background=NAVY, proportion=1.1)]}}


# ---------------------------------------------------------------- chapters

CHAPTERS = [
    ("01", "Commercial Performance", "How revenue and margin developed, and where the work is coming from.",
     "At a Glance  ·  Revenue & Margin  ·  Growth"),
    ("02", "Project Delivery", "Budget, schedule and margin risk across the project portfolio.",
     "Portfolio Health  ·  Where Projects Drift"),
    ("03", "BIM Coordination & Quality", "Clash coordination, rework and on-time delivery.",
     "Clash Coordination  ·  Rework & Delivery"),
    ("04", "Clients & Divisions", "Who we work for, and how each division compares.",
     "Clients  ·  Divisions & Geography"),
]
REPORT_TITLE = "VEC Business Report"
SUMMARY = "How VEC's BIM/VDC business performed: revenue, margin, project delivery and coordination quality."


def cover():
    global _page
    _page = pid = "page_cover"
    return {"id": pid, "kind": "cover",
            "style": {"background_color": NAVY, "background_image": "{theme.assets.images.section_bg}"},
            "layout": {"type": "row", "children": [
                blank(1.4),
                card([
                    {"type": "image", "id": "cover_logo", "proportion": 1.2, "decorative": True,
                     "source": "{theme.logo}",
                     "style": {"fit": "contain", "horizontal_align": "left", "vertical_align": "top"}},
                    text("cover_kicker", "BIM / VDC BUSINESS REPORT", "smallText", 2.3,
                         text_color=BLUE, vertical_align="bottom"),
                    heading("cover_title", REPORT_TITLE, "largeText", 1.6, as_title=True,
                            text_color=INK, vertical_align="center"),
                    rule(0.06),
                    text("cover_meta", "**{documentDateRange}**\n\n" + SUMMARY, "normalText", 2.6),
                ], background=WHITE, proportion=1.1)]}}


def agenda():
    global _page
    _page = pid = "page_agenda"
    items = []
    for n, name, desc, contents in CHAPTERS:
        items.append({"type": "row", "children": [
            heading(f"ag_n{n}", n, "largeText", 0.7, text_color=BLUE, vertical_align="top"),
            {"type": "column", "proportion": 5, "children": [
                heading(f"ag_t{n}", name, "normalText", 1, vertical_align="top"),
                text(f"ag_d{n}", f"{desc}\n\n{contents}", "smallText", 2.2)]}]})
    return {"id": pid, "kind": "content", "style": {"background_color": WHITE},
            "layout": {"type": "row", "children": [
                card(items, background=WHITE, proportion=3),
                card([
                    heading("ag_title", "Inside this report", "largeText", 4.2, as_title=True,
                            text_color=WHITE, vertical_align="bottom"),
                    rule(0.06),
                    text("ag_lead", "Four chapters: the commercial result first, then the projects, coordination "
                         "quality and clients behind it.", "normalText", 4, text_color=PANEL_TEXT,
                         vertical_align="top"),
                ], background=NAVY, proportion=2)]}}


def commercial():
    ch, k = "01  Commercial Performance", "01 — COMMERCIAL"
    return [
        chapter_page("page_chapter_01", *CHAPTERS[0]),
        kpi_page("page_glance", ch, k, "VEC at a Glance", "Headline results for the period.",
                 ["kpi_revenue", "kpi_gross_margin_pct", "kpi_billable_hours", "kpi_on_time_delivery_pct"],
                 "v_rev_margin", "revenue_margin_trend",
                 "Revenue peaks in October while margin slides from ~43% to ~39%.\n\n"
                 "One project explains it: Santa Clara Ph2 overruns after the Sep 14 scope change.\n\n"
                 "**Next:** price scope changes before the hours are worked."),
        two_chart_page("page_margin", ch, k, "Revenue & Margin",
                       "Which divisions and project types bring in revenue, and which earn the margin.",
                       ("v_rev_div", "revenue_by_division"), ("v_margin_type", "margin_by_project_type"),
                       "East runs structurally lower margin (NYC labor cost).\n\n"
                       "Industrial lags at ~23%: Newark Logistics Hub is discounted unit-price work.\n\n"
                       "**Next:** review unit-price discounts on East work."),
        two_chart_page("page_growth", ch, k, "Growth", "Where the work is coming from.",
                       ("v_rev_type_trend", "revenue_by_project_type_trend"), ("v_rev_mom", "revenue_mom_by_month"),
                       "Data center work keeps growing; Reno AI Campus mobilized Oct 1.\n\n"
                       "**Next:** staff Electrical BIM ahead of the data center ramp-up.", left_weight=1.5),
    ]


def delivery():
    ch, k = "02  Project Delivery", "02 — DELIVERY"
    return [
        chapter_page("page_chapter_02", *CHAPTERS[1]),
        kpi_page("page_portfolio", ch, k, "Portfolio Health",
                 "How many projects are running, and how many are at risk.",
                 ["kpi_active_projects", "kpi_projects_at_risk", "kpi_contract_value", "kpi_hours_variance_pct"],
                 "v_hours_plan", "hours_vs_plan",
                 "Santa Clara Ph2 is ~1,060 hours over plan; every other project is within ±4%.\n\n"
                 "**Next:** recover Santa Clara Ph2 through a change order."),
        two_chart_page("page_drift", ch, k, "Where Projects Drift", "How hours over plan turn into lost margin.",
                       ("v_margin_overrun", "margin_vs_overrun"), ("v_margin_contract", "margin_trend_by_contract"),
                       "Fixed Fee margin drops from ~41% to ~29% after Sep 14: overrun on a capped fee.\n\n"
                       "Newark is on plan but earns the lowest margin: a price issue, not delivery.\n\n"
                       "**Next:** add a scope-change clause to Fixed Fee contracts."),
    ]


def quality():
    ch, k = "03  BIM Coordination & Quality", "03 — QUALITY"
    return [
        chapter_page("page_chapter_03", *CHAPTERS[2]),
        kpi_page("page_clash", ch, k, "Clash Coordination", "BIM clashes found, resolved and still open.",
                 ["kpi_clashes_detected", "kpi_clash_resolution_rate", "kpi_clash_backlog", "kpi_rework_pct"],
                 "v_clash_trend", "clash_trend",
                 "The detected-vs-resolved gap closes after the VEC Coordination Hub went live on Sep 1.\n\n"
                 "**Next:** roll the Hub out to all remaining projects."),
        two_chart_page("page_rework", ch, k, "Rework & Delivery",
                       "What rework costs, and which service lines deliver on time.",
                       ("v_rework_project", "rework_cost_by_project"), ("v_on_time", "on_time_by_service_line"),
                       "Santa Clara Ph2 burns ~$61K in rework, about twice any other project.\n\n"
                       "Onsite QC was hit by the August laser-scanner calibration issue.\n\n"
                       "**Next:** add calibration checks to Onsite QC."),
    ]


def clients():
    ch, k = "04  Clients & Divisions", "04 — CLIENTS"
    return [
        chapter_page("page_chapter_04", *CHAPTERS[3]),
        kpi_page("page_clients", ch, k, "Clients", "Who we work for, and what we earn from them.",
                 ["kpi_effective_rate", "kpi_rate_realization_pct", "kpi_fte_deployed", "kpi_contract_value"],
                 "v_rev_client", "revenue_by_client",
                 "Westbrook Builders is the largest client; strategic clients bring ~60% of revenue.\n\n"
                 "Granite Underground earns the lowest margin (~30%) on discounted Civil Underground work."),
        two_chart_page("page_divisions", ch, k, "Divisions & Geography",
                       "How each division compares, and where the work is.",
                       ("v_div_compare", "division_comparison"), ("v_rev_state", "revenue_by_state"),
                       "East bills the same rates but earns ~10 pts less margin.\n\n"
                       "Data center work sits entirely in West and Central; Nevada is Reno AI Campus.",
                       left_weight=1.4),
    ]


def closing():
    global _page
    _page = pid = "page_actions"
    actions = [
        ("Protect margin on scope changes", "Santa Clara Ph2 explains most of the margin slide; price changes "
         "before the hours are worked."),
        ("Fix East pricing", "Same rates, ~10 pts less margin: review unit-price discounts and NYC staffing."),
        ("Scale what works", "The Coordination Hub closed the clash gap; extend it and staff Electrical BIM for "
         "the data center ramp-up."),
    ]
    items = []
    for i, (head, body) in enumerate(actions, 1):
        items.append({"type": "row", "proportion": 2, "children": [
            heading(f"{pid}_n{i}", f"0{i}", "largeText", 0.6, text_color=GREEN_ALT, vertical_align="top"),
            {"type": "column", "proportion": 6, "children": [
                heading(f"{pid}_h{i}", head, "normalText", 1, text_color=WHITE),
                text(f"{pid}_b{i}", body, "smallText", 2, text_color=PANEL_TEXT)]}]})
    items.append({"type": "text", "id": f"{pid}_pageno", "decorative": True, "proportion": 0.6,
                  "markdown": "{currentPageNumber} / {totalPages}",
                  "style": {"text_style": "smallText", "text_color": PANEL_TEXT, "horizontal_align": "right",
                            "vertical_align": "bottom"}})
    return {"id": pid, "kind": "content", "style": {"background_color": NAVY},
            "layout": {"type": "row", "children": [
                card([
                    text(f"{pid}_kicker", "WHERE TO ACT NEXT", "smallText", 3.7, text_color=GREEN_ALT,
                         vertical_align="bottom"),
                    heading(f"{pid}_title", "Three priorities", "largeText", 1.2, as_title=True,
                            text_color=WHITE),
                    rule(0.06),
                    text(f"{pid}_lead", "What the four chapters add up to.", "normalText", 3.5,
                         text_color=PANEL_TEXT, vertical_align="top"),
                ], background=NAVY, proportion=2),
                card(items, background=NAVY, proportion=3)]}}


def build():
    sections = [{"id": "section_intro", "pages": [cover(), agenda()]}]
    for (n, name, desc, _), fn in zip(CHAPTERS, [commercial, delivery, quality, clients]):
        sections.append({"id": f"section_{n}", "title": name, "description": desc, "pages": fn()})
    sections.append({"id": "section_actions", "pages": [closing()]})
    return {
        "type": "document",
        "id": "vec_business_report",
        "version": "2",
        "title": REPORT_TITLE,
        "description": SUMMARY,
        "period": {"granularity": "MONTH", "from": -5, "to": -1},
        "content": {
            "defaults": {
                "page_size": "widescreen",
                "takeaway": {"generation": {"instructions": (
                    "Act as a professional data analyst for a BIM/VDC engineering services firm. Write short "
                    "messages, max 255 characters. Explain what stands behind the numbers (projects, divisions, "
                    "service lines, scope changes) more than restating the numbers themselves.")}},
            },
            "sections": sections,
        },
    }


if __name__ == "__main__":
    out = Path(__file__).with_name("vec_business_report.json")
    out.write_text(json.dumps(build(), indent=4, ensure_ascii=False) + "\n")
    print(f"wrote {out}")
