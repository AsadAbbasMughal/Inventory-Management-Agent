import streamlit as st
import pandas as pd

from utils.database import (
    load_inventory,
    save_inventory,
    add_product,
    update_product,
    delete_product,
    search_product,
    get_low_stock,
    get_out_of_stock
)

from agent.inventory_agent import inventory_agent


# -----------------------------
# Page Configuration
# -----------------------------

st.set_page_config(
    page_title="Inventory Management Agent",
    page_icon="📦",
    layout="wide"
)


# -----------------------------
# Title
# -----------------------------

st.title("📦 Inventory Management Agent")
st.write("Manage your inventory easily with our smart inventory assistant.")


# -----------------------------
# Load Inventory
# -----------------------------

data = load_inventory()


# -----------------------------
# Sidebar Menu
# -----------------------------

st.sidebar.title("📋 Menu")

menu = st.sidebar.radio(
    "Select an option:",
    [
        "🏠 Dashboard",
        "📦 Inventory",
        "➕ Add Product",
        "✏️ Update Product",
        "🗑️ Delete Product",
        "⚠️ Low Stock",
        "🤖 Inventory Agent"
    ]
)


# =========================================================
# DASHBOARD
# =========================================================

if menu == "🏠 Dashboard":

    st.header("🏠 Dashboard")

    data = load_inventory()

    total_products = len(data)
    total_stock = int(data["Quantity"].sum())
    low_stock = len(get_low_stock())
    out_of_stock = len(get_out_of_stock())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📦 Total Products", total_products)

    with col2:
        st.metric("📊 Total Stock", total_stock)

    with col3:
        st.metric("⚠️ Low Stock", low_stock)

    with col4:
        st.metric("❌ Out of Stock", out_of_stock)

    st.divider()

    st.subheader("📋 Recent Inventory")

    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# INVENTORY
# =========================================================

elif menu == "📦 Inventory":

    st.header("📦 Inventory Management")

    data = load_inventory()

    search = st.text_input(
        "🔍 Search Product",
        placeholder="Enter product name..."
    )

    if search:
        result = search_product(search)

        if result.empty:
            st.warning("No product found.")
        else:
            st.dataframe(
                result,
                use_container_width=True,
                hide_index=True
            )

    else:
        st.dataframe(
            data,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# ADD PRODUCT
# =========================================================

elif menu == "➕ Add Product":

    st.header("➕ Add New Product")

    with st.form("add_product_form"):

        product_id = st.text_input("Product ID")
        product_name = st.text_input("Product Name")
        category = st.text_input("Category")
        quantity = st.number_input(
            "Quantity",
            min_value=0,
            step=1
        )
        price = st.number_input(
            "Price",
            min_value=0.0,
            step=100.0
        )
        supplier = st.text_input("Supplier")

        submitted = st.form_submit_button(
            "➕ Add Product"
        )

        if submitted:

            if not product_id or not product_name:
                st.error("Product ID and Product Name are required.")

            else:

                if quantity == 0:
                    status = "Out of Stock"
                elif quantity <= 5:
                    status = "Low Stock"
                else:
                    status = "In Stock"

                product = {
                    "Product_ID": product_id,
                    "Product_Name": product_name,
                    "Category": category,
                    "Quantity": quantity,
                    "Price": price,
                    "Supplier": supplier,
                    "Status": status
                }

                add_product(product)

                st.success(
                    f"{product_name} added successfully!"
                )

                st.rerun()


# =========================================================
# UPDATE PRODUCT
# =========================================================

elif menu == "✏️ Update Product":

    st.header("✏️ Update Product")

    data = load_inventory()

    product_ids = data["Product_ID"].tolist()

    if product_ids:

        selected_id = st.selectbox(
            "Select Product",
            product_ids
        )

        selected_product = data[
            data["Product_ID"] == selected_id
        ].iloc[0]

        quantity = st.number_input(
            "New Quantity",
            min_value=0,
            value=int(selected_product["Quantity"]),
            step=1
        )

        price = st.number_input(
            "New Price",
            min_value=0.0,
            value=float(selected_product["Price"]),
            step=100.0
        )

        if st.button("💾 Update Product"):

            if quantity == 0:
                status = "Out of Stock"
            elif quantity <= 5:
                status = "Low Stock"
            else:
                status = "In Stock"

            updates = {
                "Quantity": quantity,
                "Price": price,
                "Status": status
            }

            update_product(
                selected_id,
                updates
            )

            st.success("Product updated successfully!")

            st.rerun()


# =========================================================
# DELETE PRODUCT
# =========================================================

elif menu == "🗑️ Delete Product":

    st.header("🗑️ Delete Product")

    data = load_inventory()

    product_ids = data["Product_ID"].tolist()

    if product_ids:

        selected_id = st.selectbox(
            "Select Product to Delete",
            product_ids
        )

        selected_product = data[
            data["Product_ID"] == selected_id
        ].iloc[0]

        st.write(
            f"Product: **{selected_product['Product_Name']}**"
        )

        if st.button("🗑️ Delete Product"):

            delete_product(selected_id)

            st.success("Product deleted successfully!")

            st.rerun()


# =========================================================
# LOW STOCK
# =========================================================

elif menu == "⚠️ Low Stock":

    st.header("⚠️ Low Stock Products")

    low_stock = get_low_stock()

    if low_stock.empty:

        st.success("No low-stock products.")

    else:

        st.warning(
            f"{len(low_stock)} products are currently low in stock."
        )

        st.dataframe(
            low_stock,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# INVENTORY AGENT
# =========================================================

elif menu == "🤖 Inventory Agent":

    st.header("🤖 Inventory Management Agent")

    st.write(
        "Ask the agent questions about your inventory."
    )

    question = st.text_input(
        "💬 Ask a question",
        placeholder="Example: Which products are low stock?"
    )

    if st.button("🔍 Ask Agent"):

        if question.strip():

            answer = inventory_agent(question)

            st.subheader("🤖 Agent Response")

            st.code(answer)

        else:

            st.warning("Please enter a question.")