"""Regression checks for CSV quoting and the stock rules behind the dashboard."""

import csv
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent.inventory_agent import answer_question
from utils import database


def csv_record(fields):
    buffer = io.StringIO(newline="")
    csv.writer(buffer).writerow(fields)
    return buffer.getvalue().rstrip("\r\n")


class InventoryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "inventory.csv"
        file_patch = patch.object(database, "FILE_PATH", self.path)
        file_patch.start()
        self.addCleanup(file_patch.stop)
        self.path.write_text(csv_record(database.COLUMNS) + "\n", encoding="utf-8")

    def test_mixed_csv_quoting_and_read_only_load(self):
        with self.path.open("w", newline="", encoding="utf-8") as target:
            writer = csv.writer(target)
            writer.writerow([csv_record(database.COLUMNS)])
            writer.writerow([csv_record(["001", "Lamp, small", "Office", 5, 10, "A, Inc.", "Low Stock"])])
            writer.writerow(["002", 'Cable, 6"', "Accessories", 6, 2, "B, Ltd.", "Low Stock"])
        before = self.path.read_bytes()
        frame = database.load_inventory()
        self.assertEqual(frame.Product_ID.tolist(), ["001", "002"])
        self.assertEqual(frame.Product_Name.tolist(), ["Lamp, small", 'Cable, 6"'])
        self.assertEqual(frame.Status.tolist(), ["Low Stock", "In Stock"])
        self.assertEqual(before, self.path.read_bytes())

    def test_persisted_restock_and_assistant(self):
        database.add_product({"Product_ID": "003", "Product_Name": "Keyboard", "Quantity": 5, "Price": 100})
        self.assertEqual(len(database.get_low_stock()), 1)
        database.update_product("003", {"Quantity": 6, "Price": 105})
        self.assertTrue(database.get_low_stock().empty)
        answer = answer_question("How many units of Keyboard are there?")
        self.assertEqual(answer.table.iloc[0].Quantity, 6)
        self.assertIn("6 units · In Stock", answer.text)
        database.delete_product("003")
        self.assertTrue(database.load_inventory().empty)

    def test_stock_boundaries(self):
        statuses = [database.stock_status(n) for n in (0, 1, 5, 6)]
        self.assertEqual(statuses, ["Out of Stock", "Low Stock", "Low Stock", "In Stock"])


if __name__ == "__main__":
    unittest.main()
