from utils.database import (
    load_inventory,
    get_low_stock,
    get_out_of_stock
)


def inventory_agent(question):
    """
    User ke question ko samajh kar
    inventory se relevant information deta hai.
    """

    question = question.lower().strip()

    data = load_inventory()

    # Total products
    if "total product" in question or "how many product" in question:
        return f"There are {len(data)} different products in the inventory."

    # Total stock
    elif "total stock" in question or "total quantity" in question:
        total = data["Quantity"].sum()
        return f"The total quantity of all products is {total}."

    # Low stock
    elif "low stock" in question:
        low_stock = get_low_stock()

        if low_stock.empty:
            return "There are no low-stock products."

        return low_stock[
            ["Product_ID", "Product_Name", "Quantity"]
        ].to_string(index=False)

    # Out of stock
    elif "out of stock" in question:
        out_stock = get_out_of_stock()

        if out_stock.empty:
            return "There are no out-of-stock products."

        return out_stock[
            ["Product_ID", "Product_Name", "Quantity"]
        ].to_string(index=False)

    # Categories
    elif "categor" in question:
        categories = data["Category"].unique()
        return "Available categories: " + ", ".join(categories)

    # Supplier
    elif "supplier" in question:
        suppliers = data["Supplier"].unique()
        return "Available suppliers: " + ", ".join(suppliers)

    # Product search
    else:
        matching_products = data[
            data["Product_Name"]
            .str.contains(question, case=False, na=False)
        ]

        if not matching_products.empty:
            return matching_products.to_string(index=False)

        return (
            "Sorry, I could not understand your question. "
            "Try asking about total products, low stock, "
            "out of stock, categories, or suppliers."
        )