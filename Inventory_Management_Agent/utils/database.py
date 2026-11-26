import pandas as pd
from pathlib import Path


# Project folder ka path
BASE_DIR = Path(__file__).resolve().parent.parent

# Inventory CSV ka exact path
FILE_PATH = BASE_DIR / "data" / "inventory.csv"


# CSV ke columns
COLUMNS = [
    "Product_ID",
    "Product_Name",
    "Category",
    "Quantity",
    "Price",
    "Supplier",
    "Status"
]


def load_inventory():
    """Inventory CSV load karta hai."""

    # CSV read karo
    data = pd.read_csv(
        FILE_PATH,
        header=None,
        names=COLUMNS,
        skiprows=1
    )

    # Har column ke extra spaces remove karo
    for column in data.columns:
        data[column] = data[column].astype(str).str.strip()

    # Quantity ko number banao
    data["Quantity"] = pd.to_numeric(
        data["Quantity"],
        errors="coerce"
    ).fillna(0)

    # Price ko number banao
    data["Price"] = pd.to_numeric(
        data["Price"],
        errors="coerce"
    ).fillna(0)

    return data


def save_inventory(data):
    """Inventory CSV mein save karta hai."""
    data.to_csv(
        FILE_PATH,
        index=False
    )


def add_product(product):
    """New product add karta hai."""

    data = load_inventory()

    new_product = pd.DataFrame(
        [product],
        columns=COLUMNS
    )

    data = pd.concat(
        [data, new_product],
        ignore_index=True
    )

    save_inventory(data)


def update_product(product_id, updates):
    """Existing product update karta hai."""

    data = load_inventory()

    for key, value in updates.items():
        data.loc[
            data["Product_ID"] == product_id,
            key
        ] = value

    save_inventory(data)


def delete_product(product_id):
    """Product delete karta hai."""

    data = load_inventory()

    data = data[
        data["Product_ID"] != product_id
    ]

    save_inventory(data)


def search_product(product_name):
    """Product search karta hai."""

    data = load_inventory()

    return data[
        data["Product_Name"].str.contains(
            product_name,
            case=False,
            na=False
        )
    ]


def get_low_stock():
    """Low stock products return karta hai."""

    data = load_inventory()

    return data[
        data["Status"] == "Low Stock"
    ]


def get_out_of_stock():
    """Out of stock products return karta hai."""

    data = load_inventory()

    return data[
        data["Status"] == "Out of Stock"
    ]