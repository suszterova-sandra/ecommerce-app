"""
Build publisher/ecommerce_business_report.json: a GoodData document (v2) over the Ecommerce Company
(parent workspace) visualizations, styled to go with theme/conference_dark_lime_theme.json
(near-black surfaces, charcoal cards, lime accent #D4F24A, Inter).

    python3 publisher/build_ecommerce_report.py

Layout notes (same rules as build_report.py)
- No small spacer elements; spacers only for large empty areas and the accent rules.
- Page is near-black (theme page background), KPI tiles and chart cards are charcoal (CARD).
- Headings use the paragraph text styles (largeText / normalText) with bold markdown.
- Visualizations render without titles, so each card carries a centred label from analytics/visualisations/.
- The "What to look for" panels are reading guides, not data claims: AI takeaways supply the numbers.
"""
import itertools
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Colours come from the active workspace theme (documents.colors in theme/build_themes.py), so the same
# report renders dark/lime in the parent and IKEA navy/yellow in the BigBox Retailer child workspace.
# Set THEMED = False to fall back to the parent's fixed hex colours.
THEMED = True
if THEMED:
    BG, CARD, PANEL = ("{theme.colors.backgrounds.page}", "{theme.colors.backgrounds.card}",
                       "{theme.colors.backgrounds.panel}")
    LIME, TXT, TXT2, MUTED = ("{theme.colors.texts.accent}", "{theme.colors.texts.default}",
                              "{theme.colors.texts.muted}", "{theme.colors.texts.subtle}")
else:
    BG, CARD, PANEL = "#0B0D10", "#14171C", "#1B1F25"
    LIME, TXT, TXT2, MUTED = "#D4F24A", "#F2F4F7", "#9BA3AE", "#5B636E"
DATE = "date"
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


def rule(proportion):
    """Lime accent line: the theme's accent_bar image, left-aligned."""
    return {"type": "image", "id": f"{_page}_rule{next(_spacer)}", "proportion": proportion, "decorative": True,
            "source": "{theme.assets.images.accent_bar}",
            "style": {"fit": "contain", "horizontal_align": "left", "vertical_align": "center"}}


def blank(proportion):
    """Empty area that lets the page background show (non-breaking space hides the editor placeholder)."""
    return {"type": "text", "id": f"{_page}_blank{next(_spacer)}", "proportion": proportion, "decorative": True,
            "markdown": " ", "style": {"text_style": "smallText"}}


def spacer(proportion):
    """Invisible gap: a transparent 1x1 image. Images get no 'Add text here' placeholder, unlike empty text."""
    return {"type": "image", "id": f"{_page}_gap{next(_spacer)}", "proportion": proportion, "decorative": True,
            "source": "{theme.assets.images.spacer}",
            "style": {"fit": "contain", "horizontal_align": "center", "vertical_align": "center"}}


def card(children, background=CARD, proportion=None, pad=None):
    """Column with a background. The document format has no per-node padding, so `pad=(side, top, bottom)`
    insets the content with transparent spacer images."""
    if pad:
        side, top, bottom = pad
        body = {"type": "column", "proportion": 1, "children": children}
        inner = {"type": "row", "proportion": 10, "children": [spacer(side), body, spacer(side)]} if side else \
            {"type": "column", "proportion": 10, "children": children}
        children = ([spacer(top)] if top else []) + [inner] + ([spacer(bottom)] if bottom else [])
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
        heading(f"{_page}_{visualization}_lbl", TITLES[visualization].upper(), "smallText", 0.55,
                text_color=TXT2, horizontal_align="center", vertical_align="bottom"),
        {"type": "column", "proportion": 3.6, "children": [viz(f"{_page}_{visualization}", visualization)]},
    ], pad=(0, 0.35, 0.35))


def kpi_row(kpis, proportion=4.0):
    return plain_row([kpi_tile(k) for k in kpis], proportion)


def chart_card(vid, visualization, proportion=None):
    return card([
        heading(f"{vid}_lbl", TITLES[visualization], "normalText", 1, text_color=TXT,
                horizontal_align="center", vertical_align="center"),
        {"type": "column", "proportion": 8, "children": [viz(vid, visualization)]},
    ], proportion=proportion)


def insight(body, proportion=1.3, label="What to look for"):
    return card([
        heading(f"{_page}_ih", label, "normalText", 1, text_color=LIME, vertical_align="center"),
        text(f"{_page}_ib", body, "smallText", 5.5, text_color=TXT2),
    ], background=PANEL, proportion=proportion, pad=(0.07, 0.3, 0.3))


def footer(chapter):
    return {"type": "row", "proportion": 0.6, "children": [
        {"type": "image", "id": f"{_page}_logo", "proportion": 2, "decorative": True, "source": "{theme.assets.images.logo}",
         "style": {"fit": "contain", "horizontal_align": "left", "vertical_align": "bottom"}},
        {"type": "text", "id": f"{_page}_section", "proportion": 5, "decorative": True, "markdown": chapter,
         "style": {"text_style": "smallText", "horizontal_align": "center", "vertical_align": "bottom"}},
        {"type": "text", "id": f"{_page}_pageno", "proportion": 2, "decorative": True,
         "markdown": "{currentPageNumber} / {totalPages}",
         "style": {"text_style": "smallText", "horizontal_align": "right", "vertical_align": "bottom"}}]}


def content_page(page_id, chapter, kicker, title, lead, body_rows):
    global _page
    _page = page_id
    children = [
        {"type": "column", "proportion": 2.0, "children": [
            text(f"{page_id}_kicker", kicker, "smallText", 0.8, text_color=LIME, vertical_align="bottom"),
            heading(f"{page_id}_title", title, "largeText", 1.3, as_title=True, text_color=TXT,
                    vertical_align="center"),
            text(f"{page_id}_lead", lead, "normalText", 1, vertical_align="top")]},
        rule(0.05),
        *body_rows(),
        footer(chapter),
    ]
    return {"id": page_id, "kind": "content", "style": {"background_color": BG},
            "layout": {"type": "column", "children": children}}


def kpi_page(page_id, chapter, kicker, title, lead, kpis, chart, chart_vis, body):
    return content_page(page_id, chapter, kicker, title, lead, lambda: [
        kpi_row(kpis),
        plain_row([chart_card(chart, chart_vis, proportion=2.7), insight(body)], 5.0)])


def two_chart_page(page_id, chapter, kicker, title, lead, left, right, body, left_weight=1.0):
    return content_page(page_id, chapter, kicker, title, lead, lambda: [
        plain_row([chart_card(left[0], left[1], proportion=left_weight),
                   chart_card(right[0], right[1]),
                   insight(body, proportion=0.75)], 8)])


def hero_image(iid, source):
    """The GoodData rings visual as a page element; 'cover' fit keeps the glowing centre in view."""
    return {"type": "image", "id": iid, "decorative": True, "source": source,
            "style": {"fit": "cover", "horizontal_align": "center", "vertical_align": "center"}}


def chapter_page(page_id, number, name, description, contents):
    """Split layout: chapter text on solid black on the left, the rings visual on the right."""
    global _page
    _page = page_id
    return {"id": page_id, "kind": "section", "style": {"background_color": BG},
            "layout": {"type": "row", "children": [
                card([
                    spacer(0.7),
                    heading(f"{page_id}_num", number, "largeText", 2.4, text_color=LIME, vertical_align="bottom"),
                    heading(f"{page_id}_title", name, "largeText", 1.2, as_title=True,
                            text_color=TXT, vertical_align="center"),
                    rule(0.08),
                    text(f"{page_id}_desc", f"{description}\n\n**In this chapter:** {contents}",
                         "normalText", 2.0, text_color=TXT2, vertical_align="top"),
                    {"type": "image", "id": f"{page_id}_logo", "proportion": 0.6, "decorative": True, "source": "{theme.assets.images.logo}",
                     "style": {"fit": "contain", "horizontal_align": "left", "vertical_align": "bottom"}}],
                    background=BG, proportion=1, pad=(0.08, 0.3, 0.3)),
                {"type": "column", "proportion": 1.15, "children": [
                    hero_image(f"{page_id}_hero", "{theme.assets.images.section_bg}")]}]}}


# ---------------------------------------------------------------- chapters

CHAPTERS = [
    ("01", "Sales Performance", "How net sales and gross profit developed over the period.",
     "At a Glance  ·  Category Mix"),
    ("02", "Products & Brands", "Which products and brands drive sales, profit and returns.",
     "Top Performers  ·  Profit & Returns"),
    ("03", "Customers", "Who buys, how often, and where they are.",
     "Customer Health  ·  Geography & Top Customers"),
    ("04", "Orders & Fulfillment", "How orders move from placement to completion.",
     "Fulfillment Funnel  ·  Completed vs. Canceled"),
]
REPORT_TITLE = "Ecommerce Business Report"
SUMMARY = "Sales, products, customers and fulfillment across every tenant, in one view."


def cover():
    """Split layout: logo, title and period on solid black on the left, the rings visual on the right."""
    global _page
    _page = pid = "page_cover"
    return {"id": pid, "kind": "cover", "style": {"background_color": BG},
            "layout": {"type": "row", "children": [
                card([
                    spacer(2.0),
                    text("cover_kicker", "BUSINESS REPORT  ·  {documentDateRange}", "smallText", 0.6,
                         text_color=LIME, vertical_align="bottom"),
                    heading("cover_title", REPORT_TITLE, "largeText", 1.4, as_title=True,
                            text_color=TXT, vertical_align="center"),
                    rule(0.08),
                    text("cover_meta", SUMMARY, "normalText", 1.3, text_color=TXT2, vertical_align="top"),
                    {"type": "image", "id": "cover_logo", "proportion": 0.6, "decorative": True, "source": "{theme.assets.images.logo}",
                     "style": {"fit": "contain", "horizontal_align": "left", "vertical_align": "bottom"}}],
                    background=BG, proportion=1, pad=(0.08, 0.3, 0.3)),
                {"type": "column", "proportion": 1.25, "children": [
                    hero_image("cover_hero", "{theme.assets.images.cover_bg}")]}]}}


def agenda():
    global _page
    _page = pid = "page_agenda"
    items = []
    for n, name, desc, contents in CHAPTERS:
        items.append({"type": "row", "children": [
            heading(f"ag_n{n}", n, "largeText", 0.7, text_color=LIME, vertical_align="top"),
            {"type": "column", "proportion": 5, "children": [
                heading(f"ag_t{n}", name, "normalText", 1, text_color=TXT, vertical_align="top"),
                text(f"ag_d{n}", f"{desc}\n\n{contents}", "smallText", 2.2)]}]})
    return {"id": pid, "kind": "content", "style": {"background_color": BG},
            "layout": {"type": "row", "children": [
                card(items + [{"type": "image", "id": "ag_logo", "proportion": 0.5, "decorative": True, "source": "{theme.assets.images.logo}",
                     "style": {"fit": "contain", "horizontal_align": "left", "vertical_align": "bottom"}}], background=BG, proportion=3),
                card([
                    heading("ag_title", "Inside this report", "largeText", 4.2, as_title=True,
                            text_color=TXT, vertical_align="bottom"),
                    rule(0.06),
                    text("ag_lead", "Four chapters: the sales result first, then the products, customers and "
                         "orders behind it.", "normalText", 4, text_color=TXT2, vertical_align="top"),
                ], background=CARD, proportion=2, pad=(0.08, 0.3, 0.3))]}}


def sales():
    ch, k = "01  Sales Performance", "01 — SALES"
    return [
        chapter_page("page_chapter_01", *CHAPTERS[0]),
        kpi_page("page_glance", ch, k, "At a Glance", "Headline results for the period.",
                 ["net_sales_headline", "gross_profit_headline", "orders_processed_headline",
                  "active_customers_headline"],
                 "v_revenue_trend", "revenue_trend_over_time",
                 "Read revenue against order volume: revenue rising faster than orders means a higher "
                 "average basket.\n\nWatch for peaks that are not repeated the next month.\n\n"
                 "**Ask:** is growth coming from more customers or bigger orders?"),
        two_chart_page("page_mix", ch, k, "Category Mix",
                       "Which categories bring in net sales, and how this year compares with last.",
                       ("v_sales_cat", "total_net_sales_by_product_category_bar"),
                       ("v_sales_yoy", "total_net_sales_current_vs_last_year"),
                       "A few categories usually carry most of the sales.\n\n"
                       "Gaps between the current and previous period show seasonality or real change.\n\n"
                       "**Ask:** which category drives the year-on-year difference?", left_weight=1.0),
    ]


def products():
    ch, k = "02  Products & Brands", "02 — PRODUCTS"
    return [
        chapter_page("page_chapter_02", *CHAPTERS[1]),
        two_chart_page("page_top", ch, k, "Top Performers", "The products and brands that sell and earn the most.",
                       ("v_top_gp", "top_products_by_gross_profit"),
                       ("v_brands", "best_selling_product_brands"),
                       "Best sellers are not always the most profitable.\n\n"
                       "Brands high on volume but low on profit point to discounting.\n\n"
                       "**Ask:** where should promotion budget go?"),
        two_chart_page("page_profit", ch, k, "Profit & Returns",
                       "Where gross profit is earned, and which categories come back.",
                       ("v_gp_cat", "gross_profit_by_product_category"),
                       ("v_returns", "return_rate_units_by_product_category"),
                       "A category with a high return rate gives back part of its profit.\n\n"
                       "Compare each category's share of profit with its share of returns.\n\n"
                       "**Ask:** which returns are a product issue and which a sizing or description issue?"),
    ]


def customers():
    ch, k = "03  Customers", "03 — CUSTOMERS"
    return [
        chapter_page("page_chapter_03", *CHAPTERS[2]),
        kpi_page("page_customers", ch, k, "Customer Health", "How many customers buy, and how loyal they are.",
                 ["active_customers_headline", "customer_retention_rate", "customers_with_multiple_orders",
                  "average_sales_per_customer"],
                 "v_cust_activity", "customer_activity_over_time",
                 "Retention and repeat orders matter more than new sign-ups.\n\n"
                 "A dip in weekly activity often comes before a drop in sales.\n\n"
                 "**Ask:** what brings first-time buyers back for a second order?"),
        two_chart_page("page_geo", ch, k, "Geography & Top Customers", "Where customers are, and who spends the most.",
                       ("v_country", "sales_and_active_customers_by_customer_country_089ecfae"),
                       ("v_top_cust", "top_10_customers_by_revenue"),
                       "Countries with many customers but low sales are an upsell opportunity.\n\n"
                       "Check how much revenue depends on the top 10 customers.\n\n"
                       "**Ask:** how exposed are we to a few large buyers?", left_weight=1.2),
    ]


def orders():
    ch, k = "04  Orders & Fulfillment", "04 — ORDERS"
    return [
        chapter_page("page_chapter_04", *CHAPTERS[3]),
        two_chart_page("page_funnel", ch, k, "Fulfillment Funnel", "How orders move from placement to completion.",
                       ("v_funnel", "order_fulfillment_funnel"),
                       ("v_status", "order_status_breakdown"),
                       "The biggest step down in the funnel is where orders are lost.\n\n"
                       "**Ask:** is the drop-off in payment, stock or delivery?"),
        two_chart_page("page_cancel", ch, k, "Completed vs. Canceled", "Order outcomes over time and by state.",
                       ("v_cancel", "completed_vs_canceled_orders_trend"),
                       ("v_states", "top_5_states_by_number_of_orders"),
                       "Cancellation spikes usually line up with stock-outs or delivery delays.\n\n"
                       "**Ask:** do the top states also have the most cancellations?", left_weight=1.4),
    ]


def closing():
    global _page
    _page = pid = "page_actions"
    actions = [
        ("Grow the basket, not just the base", "Push the categories and brands that combine volume with margin."),
        ("Win the second order", "Retention and repeat purchases are the cheapest growth lever."),
        ("Close the fulfillment gap", "Fix the funnel step with the biggest drop-off and track cancellations weekly."),
    ]
    items = []
    for i, (head, body) in enumerate(actions, 1):
        items.append({"type": "row", "proportion": 2, "children": [
            heading(f"{pid}_n{i}", f"0{i}", "largeText", 0.6, text_color=LIME, vertical_align="top"),
            {"type": "column", "proportion": 6, "children": [
                heading(f"{pid}_h{i}", head, "normalText", 1, text_color=TXT),
                text(f"{pid}_b{i}", body, "smallText", 2, text_color=TXT2)]}]})
    items.append({"type": "text", "id": f"{pid}_pageno", "decorative": True, "proportion": 0.6,
                  "markdown": "{currentPageNumber} / {totalPages}",
                  "style": {"text_style": "smallText", "text_color": MUTED, "horizontal_align": "right",
                            "vertical_align": "bottom"}})
    return {"id": pid, "kind": "content",
            "style": {"background_color": BG, "background_image": "{theme.assets.images.section_bg}"},
            "layout": {"type": "row", "children": [
                card([
                    text(f"{pid}_kicker", "WHERE TO ACT NEXT", "smallText", 3.7, text_color=LIME,
                         vertical_align="bottom"),
                    heading(f"{pid}_title", "Three priorities", "largeText", 1.2, as_title=True, text_color=TXT),
                    rule(0.06),
                    text(f"{pid}_lead", "What the four chapters add up to.", "normalText", 2.9,
                         text_color=TXT2, vertical_align="top"),
                    {"type": "image", "id": f"{pid}_logo", "proportion": 0.6, "decorative": True, "source": "{theme.assets.images.logo}",
                     "style": {"fit": "contain", "horizontal_align": "left", "vertical_align": "bottom"}}
                ], background=BG, proportion=2),
                card(items, background=CARD, proportion=3, pad=(0.06, 0.4, 0.3))]}}


def build():
    sections = [{"id": "section_intro", "pages": [cover(), agenda()]}]
    for (n, name, desc, _), fn in zip(CHAPTERS, [sales, products, customers, orders]):
        sections.append({"id": f"section_{n}", "title": name, "description": desc, "pages": fn()})
    sections.append({"id": "section_actions", "pages": [closing()]})
    return {
        "type": "document",
        "id": "ecommerce_business_report",
        "version": "2",
        "title": REPORT_TITLE,
        "description": SUMMARY,
        "period": {"granularity": "MONTH", "from": -5, "to": -1},
        "content": {
            "defaults": {
                "page_size": "widescreen",
                "takeaway": {"generation": {"instructions": (
                    "Act as a professional data analyst for an ecommerce company. Write short messages, max 255 "
                    "characters. Explain what stands behind the numbers (categories, brands, customer segments, "
                    "countries, order outcomes) more than restating the numbers themselves.")}},
            },
            "sections": sections,
        },
    }


if __name__ == "__main__":
    out = Path(__file__).with_name("ecommerce_business_report.json")
    out.write_text(json.dumps(build(), indent=4, ensure_ascii=False) + "\n")
    print(f"wrote {out}")
