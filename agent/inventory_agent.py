"""Answer supported inventory questions with a few predictable keyword rules."""

from dataclasses import dataclass
import re

import pandas as pd

from utils.database import load_inventory


@dataclass
class Answer:
    text: str
    table: pd.DataFrame | None = None


def _product_matches(query, data):
    names = data["Product_Name"].str.casefold()
    ids = data["Product_ID"].str.casefold()
    direct = data[(names == query) | (ids == query)]
    if not direct.empty:
        return direct

    # A full product name or ID can also occur inside a question.
    def mentioned(value):
        return bool(value and re.search(rf"(?<!\w){re.escape(value)}(?!\w)", query))

    matches = data[names.map(mentioned).astype(bool) | ids.map(mentioned).astype(bool)]
    if matches.empty:
        matches = data[names.str.contains(query, regex=False, na=False)]
    return matches


def answer_question(question, data=None):
    """Return a sentence and, for product results, a table the UI can render."""
    if data is None:
        data = load_inventory()
    query = " ".join(question.casefold().split()).strip("?!")
    keywords = query.replace("-", " ")
    if query:
        for phrase, status in [("out of stock", "Out of Stock"), ("low stock", "Low Stock")]:
            if phrase in keywords:
                rows = data.loc[data["Status"] == status, ["Product_ID", "Product_Name", "Quantity"]]
                if rows.empty:
                    return Answer(f"No products are currently {phrase}.")
                rows = rows.sort_values(["Quantity", "Product_Name"], kind="stable")
                label = "product is" if len(rows) == 1 else "products are"
                return Answer(f"{len(rows)} {label} currently {phrase}.", rows)

        if "categor" in keywords or "supplier" in keywords:
            column = "Category" if "categor" in keywords else "Supplier"
            label = "categories" if column == "Category" else "suppliers"
            values = sorted(set(data[column]) - {""}, key=str.casefold)
            if not values:
                return Answer(f"No {label} are listed yet.")
            return Answer(f"Available {label}: " + ", ".join(values) + ".")

        if "total product" in keywords or "how many product" in keywords:
            label = "product" if len(data) == 1 else "products"
            return Answer(f"The inventory contains {len(data):,} {label}.")
        if "total stock" in keywords or "total quantity" in keywords or "total units" in keywords:
            quantity = int(data["Quantity"].sum())
            label = "unit" if quantity == 1 else "units"
            return Answer(f"The inventory holds {quantity:,} {label} in total.")

        rows = _product_matches(query, data)
        if not rows.empty:
            if len(rows) == 1:
                row = rows.iloc[0]
                units = "unit" if row["Quantity"] == 1 else "units"
                return Answer(f"{row['Product_Name']} has {row['Quantity']} {units} · {row['Status']}.", rows)
            return Answer(f"Found {len(rows)} matching products.", rows)

    return Answer(
        "Try a product name or ID, or ask a question like “Which products are low stock?”, "
        "“What is the total stock?” or “List suppliers.”"
    )


def inventory_agent(question):
    """Keep the original text interface available for scripts and notebooks."""
    answer = answer_question(question)
    if answer.table is None:
        return answer.text
    return answer.text + "\n" + answer.table.to_string(index=False)
