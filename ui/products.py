"""Product forms. Only a confirmed save or deletion writes to the inventory."""

from html import escape
from math import isfinite

import streamlit as st

from ui.shared import status_badge
from utils.database import add_product, delete_product, stock_status, update_product


def _finish(message=None):
    if message:
        st.session_state["notice"] = message
    st.session_state.pop("product_action", None)
    st.session_state.pop("product_id", None)
    st.rerun()


def _stock_fields(key, quantity=0, price=0.0):
    left, right = st.columns(2)
    with left:
        quantity = st.number_input(
            "Quantity", min_value=0, value=int(quantity), step=1, key=f"{key}_quantity"
        )
        if quantity is None:
            st.error("Enter the number of units, including 0 for none.")
        else:
            units = "unit" if quantity == 1 else "units"
            st.html(f'<small>{quantity:,} {units} · </small>{status_badge(stock_status(quantity))}')

    with right:
        price = st.number_input(
            "Price", min_value=0.0, value=float(price), step=0.01, key=f"{key}_price"
        )
        if price is None or not isfinite(price):
            st.error("Enter a price of 0 or higher.")

    return quantity, price


def _valid_numbers(quantity, price):
    return quantity is not None and price is not None and isfinite(price)


def _add(data):
    st.title("Add product")
    with st.container(border=True, width=780, key="panel_add"):
        st.subheader("Product details", anchor=False)
        left, right = st.columns(2)
        with left:
            product_id = st.text_input("Product ID", placeholder="e.g. P016", key="add_id").strip()
            id_error = st.empty()
        with right:
            name = st.text_input("Product name", placeholder="e.g. Wireless mouse", key="add_name").strip()
            name_error = st.empty()

        left, right = st.columns(2)
        category = left.text_input("Category (optional)", key="add_category").strip()
        supplier = right.text_input("Supplier (optional)", key="add_supplier").strip()

        st.divider()
        st.subheader("Stock and price", anchor=False)
        quantity, price = _stock_fields("add")
        st.divider()

        with st.container(horizontal=True):
            save = st.button("Add product", type="primary", key="save_new_product")
            if st.button("Cancel", key="cancel_add"):
                _finish()
        if save:
            duplicate = product_id.casefold() in set(data["Product_ID"].str.casefold())
            if not product_id:
                id_error.error("Enter a product ID, such as P016.")
            elif duplicate:
                id_error.error("This ID is already in use. Enter a unique product ID.")
            if not name:
                name_error.error("Enter a name so people can find this product.")
            if product_id and not duplicate and name and _valid_numbers(quantity, price):
                add_product({
                    "Product_ID": product_id, "Product_Name": name,
                    "Category": category, "Supplier": supplier,
                    "Quantity": quantity, "Price": price, "Status": stock_status(quantity),
                })
                _finish(f"{name} added · {stock_status(quantity)}")


def _identity(product):
    name = escape(str(product["Product_Name"]))
    details = [product["Product_ID"], product["Category"], product["Supplier"]]
    details_html = " · ".join(escape(str(value)) for value in details if value)
    st.html(f"<h2>{name}</h2><p>{details_html}</p>")


def _edit(product):
    product_id = product["Product_ID"]
    st.title("Update stock")
    with st.container(border=True, width=780, key="panel_edit"):
        _identity(product)
        quantity, price = _stock_fields(f"edit_{product_id}", product["Quantity"], product["Price"])
        st.divider()
        with st.container(horizontal=True):
            save = st.button("Save changes", type="primary", key="save_stock")
            if st.button("Cancel", key="cancel_edit"):
                _finish()
        if save and _valid_numbers(quantity, price):
            update_product(product_id, {"Quantity": quantity, "Price": price})
            units = "unit" if quantity == 1 else "units"
            _finish(f'{product["Product_Name"]} updated · {quantity:,} {units} · {stock_status(quantity)}')


def _delete(product):
    st.title("Delete product?")
    with st.container(border=True, width=780, key="panel_delete"):
        _identity(product)
        st.warning("Deleting this product permanently removes its inventory record.")
        with st.container(horizontal=True):
            if st.button("Cancel", key="cancel_delete"):
                _finish()
            if st.button("Delete product", key="confirm_delete_product"):
                delete_product(product["Product_ID"])
                _finish(f'{product["Product_Name"]} deleted.')


def render_product_form(data):
    """Render the action opened from the dashboard, inventory or alerts."""
    action = st.session_state["product_action"]
    try:
        if action == "add":
            _add(data)
            return

        selected = data[data["Product_ID"] == st.session_state.get("product_id")]
        if len(selected) != 1:
            st.warning("This product could not be uniquely located. Return to the list and select it again.")
            if st.button("Back to list"):
                _finish()
            return

        if action == "edit":
            _edit(selected.iloc[0])
        elif action == "delete":
            _delete(selected.iloc[0])
    except (ValueError, OSError) as error:
        st.error(f"The change could not be saved. {error}")
