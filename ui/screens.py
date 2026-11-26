"""Product browsing, filtered stock alerts, and the inventory question screen."""

import streamlit as st

from agent.inventory_agent import answer_question
from ui.shared import attention_rows, esc, open_product, status_badge


STATUSES = ("In Stock", "Low Stock", "Out of Stock")
PAGE_SIZE = 20
EXAMPLES = (
    "Which products are low stock?",
    "What is the total stock?",
    "List suppliers",
)

TABLE_STYLES = """
<style>
.inventory-catalogue {max-width:100%;overflow-x:auto;border:1px solid #e0e6e1;border-radius:12px}
.inventory-catalogue:focus-visible {outline:3px solid #247788;outline-offset:2px}
.inventory-catalogue table {width:100%;border-collapse:collapse;font-size:.9rem;line-height:1.4}
.inventory-catalogue th,.inventory-catalogue td {padding:.7rem .85rem;vertical-align:middle;text-align:left;border:0}
.inventory-catalogue thead th {background:#f0f3ed;color:#435b59;font-weight:600;white-space:nowrap}
.inventory-catalogue tbody tr+tr {border-top:1px solid #e4e9e3}
.inventory-catalogue tbody tr:hover {background:#fafbf7}
.inventory-catalogue tbody th {color:#1a3940;font-weight:600;min-width:9rem}
.inventory-catalogue .product-id {display:block;font-weight:400;color:#536964;font-size:.75rem;margin-top:.16rem}
.inventory-catalogue .number {text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.inventory-catalogue .status-cell {white-space:nowrap}
</style>
"""


def _remember(name):
    """Widget keys can disappear when a page is hidden. Keep the user's value."""
    st.session_state[name] = st.session_state["_" + name]


def _restore(name, default=None):
    st.session_state.setdefault("_" + name, st.session_state.get(name, default))


def _filters_changed(name):
    _remember(name)
    st.session_state["catalogue_page"] = 0


def _clear_filters():
    for name, value in (("product_query", ""), ("category_filter", None), ("status_filter", None)):
        st.session_state[name] = value
        st.session_state["_" + name] = value
    st.session_state["catalogue_page"] = 0


def _product_table(data):
    """Render all supplied inventory fields, with a shorter table for stock answers."""
    columns = [name for name in ("Category", "Quantity", "Price", "Supplier", "Status") if name in data]
    headings = ['<th scope="col">Product / ID</th>']
    for name in columns:
        css_class = ' class="number"' if name in ("Quantity", "Price") else ""
        headings.append(f'<th scope="col"{css_class}>{name}</th>')

    rows = []
    for row in data.itertuples(index=False):
        cells = [f'<th scope="row">{esc(row.Product_Name)}<span class="product-id">{esc(row.Product_ID)}</span></th>']
        for name in columns:
            value = getattr(row, name)
            if name == "Status":
                cells.append(f'<td class="status-cell">{status_badge(value)}</td>')
            elif name == "Quantity":
                cells.append(f'<td class="number">{value:,}</td>')
            elif name == "Price":
                cells.append(f'<td class="number">{value:,.2f}</td>')
            else:
                cells.append(f'<td>{esc(value) or "—"}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")

    st.html(TABLE_STYLES + (
        '<div class="inventory-catalogue" role="region" aria-label="Product table, scroll for more columns" tabindex="0">'
        '<table aria-label="Inventory products"><thead><tr>' + "".join(headings) + "</tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table></div>"
    ))


def _change_page(page):
    st.session_state["catalogue_page"] = page


def inventory(data):
    if data.empty:
        with st.container(border=True, key="panel_catalogue_empty"):
            st.subheader("Your inventory is empty")
            st.button("Add your first product", on_click=open_product, args=("add",))
        return

    categories = sorted(data["Category"].unique(), key=str.casefold)
    if st.session_state.get("category_filter") not in [None, *categories]:
        st.session_state["category_filter"] = None
        st.session_state.pop("_category_filter", None)

    _restore("product_query", "")
    _restore("category_filter")
    _restore("status_filter")
    with st.container(border=True, key="panel_catalogue_filters"):
        search_col, cat_col, status_col, clear_col = st.columns([2.1, 1.45, 1.3, 1.15], vertical_alignment="bottom")
        query = search_col.text_input(
            "Search products", placeholder="Search by product name", key="_product_query",
            on_change=_filters_changed, args=("product_query",),
        )
        category = cat_col.selectbox(
            "Category", categories, index=None, placeholder="All categories",
            format_func=lambda value: value or "Uncategorized", key="_category_filter",
            on_change=_filters_changed, args=("category_filter",),
        )
        status = status_col.selectbox(
            "Stock status", STATUSES, index=None, placeholder="All statuses", key="_status_filter",
            on_change=_filters_changed, args=("status_filter",),
        )
        clear_col.button(
            "Clear filters", on_click=_clear_filters, width="stretch",
            disabled=not (query or category is not None or status),
        )

    results = data[data["Product_Name"].str.contains(query.strip(), case=False, regex=False, na=False)]
    if category is not None:
        results = results[results["Category"] == category]
    if status:
        results = results[results["Status"] == status]

    if results.empty:
        with st.container(border=True, key="panel_catalogue_no_match"):
            st.subheader("No matching products")
            st.write("Try a different product name or clear the filters to see your inventory.")
        return

    with st.container(border=True, key="panel_catalogue_table"):
        st.subheader("Product catalogue")
        st.caption(f"Showing {len(results):,} of {len(data):,} products")
        names = dict(zip(results["Product_ID"], results["Product_Name"]))
        if st.session_state.get("catalogue_selection") not in names:
            st.session_state["catalogue_selection"] = None
            st.session_state.pop("_catalogue_selection", None)
        _restore("catalogue_selection")
        select_col, edit_col, delete_col = st.columns([3, 1, 1], vertical_alignment="bottom")
        product = select_col.selectbox(
            "Manage a product", list(names), index=None, placeholder="Choose a product",
            format_func=lambda value: f"{names[value]} · {value}", key="_catalogue_selection",
            on_change=_remember, args=("catalogue_selection",),
        )
        edit_col.button("Edit product", width="stretch", disabled=product is None,
                        on_click=open_product, args=("edit", product))
        delete_col.button("Delete product", width="stretch", disabled=product is None,
                          on_click=open_product, args=("delete", product))

        last_page = (len(results) - 1) // PAGE_SIZE
        page = min(st.session_state.get("catalogue_page", 0), last_page)
        start = page * PAGE_SIZE
        _product_table(results.iloc[start:start + PAGE_SIZE])
        if last_page:
            previous, counter, following = st.columns([1, 2, 1], vertical_alignment="center")
            previous.button("Previous", on_click=_change_page, args=(page - 1,), disabled=page == 0)
            counter.caption(f"Page {page + 1} of {last_page + 1}")
            following.button("Next", on_click=_change_page, args=(page + 1,), disabled=page == last_page)


def alerts(data):
    allowed = ("Out of Stock", "Low Stock")
    counts = data["Status"].value_counts()
    with st.container(border=True, key="panel_alerts"):
        # Dashboard shortcuts set this persistent value before navigating to Alerts.
        st.session_state["_alert_status"] = st.session_state.get("alert_status", allowed[0])
        status = st.radio(
            "Show alerts", allowed, key="_alert_status", horizontal=True,
            format_func=lambda value: f"{value} ({counts.get(value, 0)})",
            on_change=_remember, args=("alert_status",),
        )
        rows = data[data["Status"] == status].sort_values(["Quantity", "Product_Name"], kind="stable")
        if data.empty:
            st.subheader("Your inventory is empty")
            st.button("Add your first product", on_click=open_product, args=("add",))
        elif rows.empty:
            st.success("No products are out of stock." if status == "Out of Stock" else
                       "No products are low on stock.")
        else:
            st.caption("Products with zero units." if status == "Out of Stock" else
                       "Products with 1–5 units, lowest quantity first.")
            attention_rows(rows, "stock_alerts")


def _ask_example(question):
    st.session_state["assistant_input"] = question
    st.session_state["assistant_question"] = question


def assistant(data):
    st.session_state.setdefault("assistant_input", st.session_state.get("assistant_question", ""))
    with st.container(border=True, key="panel_question"):
        with st.form("ask_inventory", border=False):
            question = st.text_input(
                "Ask about your inventory", key="assistant_input",
                placeholder="Ask about stock levels, suppliers, or enter a product name",
            )
            submitted = st.form_submit_button("Ask assistant", type="primary")
        if submitted:
            st.session_state["assistant_question"] = question.strip()
            if not question.strip():
                st.warning("Enter a question or choose an example below.")

        st.caption("Try a question")
        for col, example in zip(st.columns(3), EXAMPLES):
            col.button(example, on_click=_ask_example, args=(example,), width="stretch")

    question = st.session_state.get("assistant_question")
    if question:
        answer = answer_question(question, data)
        with st.container(border=True, key="panel_answer"):
            st.subheader("Answer")
            st.html(f"<p><strong>{esc(question)}</strong></p><p>{esc(answer.text)}</p>")
            if answer.table is not None and not answer.table.empty:
                _product_table(answer.table)
