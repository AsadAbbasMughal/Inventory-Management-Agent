"""Run from the project root with python -m streamlit run app.py."""

from pathlib import Path

import streamlit as st

from ui import screens
from ui.dashboard import dashboard
from ui.products import render_product_form
from ui.shared import esc, icon, open_product, svg_image
from utils.database import load_inventory


st.set_page_config(page_title="Inventory Management Agent", page_icon=":material/deployed_code:",
                   layout="wide", initial_sidebar_state="auto")
ASSETS = Path(__file__).parent / "ui"
st.html(ASSETS / "theme.css")


def render_screen(route, title, subtitle, render):
    state = st.session_state
    if state.get("last_route") != route:
        state.pop("product_action", None)
        state.pop("product_id", None)
        state.pop("notice", None)
        state.last_route = route

    st.html(f'<div class="workspace-bar"><span>{icon("grid", 16)} Workspace '
            f'<i>/</i> <b>{esc(route)}</b></span>'
            f'<span class="local-source">{icon("database", 15)} Local inventory</span></div>')
    try:
        data = load_inventory()
    except (ValueError, OSError) as error:
        st.error(f"Could not open data/inventory.csv. {error}")
        return

    if state.get("product_action"):
        render_product_form(data)
        return

    with st.container(key="page_heading"):
        title_column, action_column = st.columns([3.2, 1], vertical_alignment="center")
        with title_column:
            st.html(f'<h1 class="page-title">{esc(title)}</h1><p class="page-subtitle">{esc(subtitle)}</p>')
        if route in ("Dashboard", "Inventory"):
            with action_column:
                st.button("Add product", icon=":material/add:", type="primary",
                          key="header_add", on_click=open_product, args=("add",))
    if state.get("notice"):
        st.success(state.pop("notice"))
    render(data)


def overview():
    render_screen("Dashboard", "Inventory overview", "Your stock levels and the products that need attention.",
                  lambda data: dashboard(data, pages["Stock Alerts"]))


def catalogue():
    render_screen("Inventory", "Inventory", "Find a product, check its details or update its stock.", screens.inventory)


def alerts():
    render_screen("Stock Alerts", "Stock alerts", "Review products that are out of stock or running low.", screens.alerts)


def assistant():
    render_screen("Inventory Assistant", "Inventory assistant", "Ask a question about the products in your inventory.",
                  screens.assistant)


destinations = [
    ("Dashboard", overview, "space_dashboard", "dashboard"),
    ("Inventory", catalogue, "inventory_2", "inventory"),
    ("Stock Alerts", alerts, "notification_important", "stock-alerts"),
    ("Inventory Assistant", assistant, "forum", "assistant"),
]
pages = {
    title: st.Page(view, title=title, icon=f":material/{symbol}:", url_path=slug, default=(title == "Dashboard"))
    for title, view, symbol, slug in destinations
}
page = st.navigation(list(pages.values()), position="hidden")
with st.sidebar:
    st.html(f'<div class="brand"><span>{icon("box", 33)}</span><strong>Inventory<br>'
            'Management Agent</strong></div>')
    with st.container(key="workspace_nav"):
        for title, target in pages.items():
            with st.container(key="nav_current" if page.title == title else "nav_" + target.url_path):
                st.page_link(target, label=title)
    artwork = svg_image((ASSETS / "cartons.svg").read_text(encoding="utf-8"))
    st.html(f'<div class="sidebar-foot">{artwork}</div>')
page.run()
