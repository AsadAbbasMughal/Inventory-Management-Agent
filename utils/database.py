"""Read and write the seven-column inventory CSV used by the app."""

import csv
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
FILE_PATH = BASE_DIR / "data" / "inventory.csv"
COLUMNS = ["Product_ID", "Product_Name", "Category", "Quantity", "Price", "Supplier", "Status"]

# Streamlit can run two sessions in different threads of the same process.
_inventory_lock = RLock()


def stock_status(quantity):
    if quantity == 0:
        return "Out of Stock"
    if quantity <= 5:
        return "Low Stock"
    return "In Stock"


def _prepare_inventory(data):
    """Use the same field types and stock rule for reads and writes."""
    data = data.loc[:, COLUMNS].copy()
    for column in ["Product_ID", "Product_Name", "Category", "Supplier"]:
        data[column] = data[column].astype("string").fillna("").str.strip()

    for column in ["Quantity", "Price"]:
        numbers = pd.to_numeric(data[column], errors="coerce")
        if (numbers.isna() | (numbers < 0) | (numbers == float("inf"))).any():
            raise ValueError(f"{column} must contain a non-negative number for every product.")
        if column == "Quantity":
            if ((numbers % 1 != 0) | (numbers > 2**63 - 1)).any():
                raise ValueError("Quantity must be a whole number within the supported range.")
            data[column] = numbers.astype("int64")
        else:
            data[column] = numbers.astype(float)

    data["Status"] = data["Quantity"].map(stock_status)
    return data


def load_inventory():
    """Accept standard CSV and records that were exported as a single CSV field."""
    rows = []
    with _inventory_lock, FILE_PATH.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, strict=True)
        header_read = False
        try:
            for fields in reader:
                if not fields:
                    continue
                if len(fields) == 1:
                    # The original seed wraps even the comma-separated header.
                    fields = next(csv.reader([fields[0]], strict=True), [])
                if not header_read:
                    if [field.strip() for field in fields] != COLUMNS:
                        raise ValueError("The CSV header does not match the seven inventory columns.")
                    header_read = True
                    continue
                if len(fields) != len(COLUMNS):
                    raise ValueError(f"CSV line {reader.line_num} must contain seven fields.")
                rows.append(fields)
        except csv.Error as error:
            raise ValueError(f"Invalid CSV quoting near line {reader.line_num}.") from error

    return _prepare_inventory(pd.DataFrame(rows, columns=COLUMNS))


def save_inventory(data):
    """Replace the file only after a complete, standard CSV has been written."""
    with _inventory_lock:
        data = _prepare_inventory(data)
        temp_path = None
        try:
            with NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="", dir=FILE_PATH.parent, delete=False
            ) as target:
                temp_path = Path(target.name)
                data.to_csv(target, index=False)
            os.replace(temp_path, FILE_PATH)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)


def add_product(product):
    with _inventory_lock:
        data = load_inventory()
        product = dict(product)
        product_id = str(product.get("Product_ID", "")).strip()
        if not product_id or not str(product.get("Product_Name", "")).strip():
            raise ValueError("Enter a product ID and name.")
        if data["Product_ID"].str.casefold().eq(product_id.casefold()).any():
            raise ValueError(f"Product ID {product_id} already exists. Choose a unique ID.")
        new_row = _prepare_inventory(pd.DataFrame([product], columns=COLUMNS))
        save_inventory(pd.concat([data, new_row], ignore_index=True))


def _product_index(data, product_id):
    matches = data.index[data["Product_ID"] == product_id]
    if len(matches) == 0:
        raise ValueError("This product is no longer in the inventory.")
    if len(matches) > 1:
        raise ValueError("This ID belongs to more than one product. Give each record a unique ID before editing.")
    return matches[0]


def update_product(product_id, updates):
    with _inventory_lock:
        data = load_inventory()
        index = _product_index(data, product_id)
        # Older callers also pass Status. It is always derived from the new quantity.
        row = data.loc[index].to_dict()
        for column in ["Quantity", "Price"]:
            if column in updates:
                row[column] = updates[column]
        updated = _prepare_inventory(pd.DataFrame([row])).iloc[0]
        for column in ["Quantity", "Price", "Status"]:
            data.at[index, column] = updated[column]
        save_inventory(data)


def delete_product(product_id):
    with _inventory_lock:
        data = load_inventory()
        save_inventory(data.drop(index=_product_index(data, product_id)))


def search_product(product_name):
    data = load_inventory()
    return data[data["Product_Name"].str.contains(product_name, case=False, regex=False, na=False)]


def get_low_stock():
    data = load_inventory()
    return data[data["Status"] == "Low Stock"]


def get_out_of_stock():
    data = load_inventory()
    return data[data["Status"] == "Out of Stock"]
