"""Dashboard summaries and links into the work that needs doing."""

import streamlit as st

from ui.shared import attention_rows, esc, icon, open_product


def metric_cards(data, counts, alert_page):
    cards = [
        ("Total products", len(data), "box", "catalog", "Distinct products", None),
        ("Total units", int(data.Quantity.sum()), "layers", "units", "Units on hand", None),
        ("Low stock", counts.get("Low Stock", 0), "alert", "low", "1–5 units remaining", "Low Stock"),
        ("Out of stock", counts.get("Out of Stock", 0), "empty", "out", "0 units remaining", "Out of Stock"),
    ]
    with st.container(key="metrics"):
        for column, (label, number, glyph, tone, subtitle, status) in zip(st.columns(4), cards):
            with column, st.container(key=f"kpi_{tone}"):
                arrow = icon("arrow", 16) if status else ""
                st.html(
                    f'<div class="metric-card {tone}"><div class="metric-label">'
                    f'<span class="metric-icon">{icon(glyph, 20)}</span>{label}'
                    f'<span class="metric-arrow">{arrow}</span></div>'
                    f'<strong>{number:,}</strong><small>{subtitle}</small></div>'
                )
                if status and st.button(f"View {label.lower()} products", key=f"view_{tone}"):
                    st.session_state.alert_status = status
                    st.switch_page(alert_page)


def stock_health(data, counts):
    st.html('<h2 class="panel-title">Stock health</h2><p class="panel-note">Products by stock status</p>')
    total = len(data)
    palette = [("In Stock", "#348676"), ("Low Stock", "#E8AD4D"), ("Out of Stock", "#CF7063")]
    offset = 0
    stops, legend = [], []
    for label, color in palette:
        count = counts.get(label, 0)
        percent = count * 100 / total if total else 0
        if count:
            stops.append(f"{color} {offset:.8f}% {offset + percent:.8f}%")
        offset += percent
        legend.append(f'<li><i style="background:{color}"></i><span>{label}</span>'
                      f'<b>{count:,}</b></li>')
    fill = "conic-gradient(" + ", ".join(stops) + ")" if len(stops) > 1 else (
        stops[0].split()[0] if stops else "#E7EBE7"
    )
    st.html(
        f'<div class="health-ring" aria-hidden="true" style="background:{fill}">'
        f'<div><strong>{total:,}</strong><small>products</small></div></div>'
        '<ul aria-label="Products by stock status" class="health-list">' + "".join(legend) + '</ul>'
    )



def by_category(data):
    groups = data.assign(Category=data.Category.replace("", "Uncategorized")).groupby("Category").Quantity.sum()
    groups = groups.sort_values(ascending=False, kind="stable")
    largest = groups.max()
    bars = []
    for category, units in groups.items():
        width = 100 * units / largest if largest else 0
        bars.append(f'<div class="category-entry"><div><span>{esc(category)}</span><b>{units:,}</b></div>'
                    f'<div class="category-track"><i style="width:{width:.3f}%"></i></div></div>')
    with st.container(border=True, key="category_panel"):
        st.html('<h2 class="panel-title">Stock by category</h2><p class="panel-note">Units on hand</p>'
                '<div class="category-grid">' + "".join(bars) + '</div>')


def dashboard(data, alert_page):
    counts = data.Status.value_counts()
    metric_cards(data, counts, alert_page)
    work = data[data.Quantity <= 5].sort_values(["Quantity", "Product_Name"], kind="stable")
    with st.container(key="dashboard_body"):
        queue, health = st.columns([1.85, 1], gap="medium")
        with queue, st.container(border=True, key="attention_panel"):
            st.html(f'<div class="panel-heading"><h2 class="panel-title">Needs attention</h2>'
                    f'<span class="count-pill">{len(work)}</span></div>'
                    '<p class="panel-note">Lowest quantities first</p>')
            if data.empty:
                st.info("Your inventory is empty.")
                st.button("Add your first product", on_click=open_product, args=("add",))
            elif work.empty:
                st.success("All products have more than 5 units.")
            else:
                attention_rows(work, "dashboard")
        with health, st.container(border=True, key="health_panel"):
            stock_health(data, counts)
    if not data.empty:
        by_category(data)
