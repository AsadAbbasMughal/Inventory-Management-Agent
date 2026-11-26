# Inventory Management Agent

## How the app works

Streamlit reruns the active screen after an interaction. On each render, app.py reads the current inventory through utils/database.py. The dashboard, alerts and assistant read the same data. A successful product change saves the CSV, returns the user to the originating screen and displays confirmation. Session state remembers interface choices such as the selected alert filter.

## Files for a code walkthrough

| File | Responsibility |
| --- | --- |
| app.py | Set up four page routes, the sidebar, page headings, product actions and confirmation messages. |
| ui/dashboard.py | Compute dashboard counts, show the attention queue, draw the labeled stock-health ring and aggregate units by category. |
| ui/screens.py | Search/filter inventory, manage product selection, show low/out-of-stock lists and display assistant questions and answers. |
| ui/products.py | Validate add fields, preview a quantity change, save updates and confirm or cancel deletion. |
| ui/shared.py | Render status badges, consistent icons and attention rows. Open product actions using the selected ID. |
| ui/theme.css, ui/cartons.svg and .streamlit/config.toml | Style native widgets, desktop and phone layouts, focus states and the sidebar. |
| utils/database.py | Parse and validate CSV data; derive stock status; add, update and delete products. |
| agent/inventory_agent.py | Match supported phrases or product names/IDs and return a sentence and optional table. The inventory_agent function also returns a text answer for earlier callers. |
| data/inventory.csv | Persistent stock records. The supplied seed is preserved. |

## Data model

| Column | Meaning |
| --- | --- |
| Product_ID | Text identifier. New IDs are required and unique, including across capitalization differences. |
| Product_Name | Required product name. The inventory search matches literal, case-insensitive substrings. |
| Category | Optional group. A blank category is shown as Uncategorized in category summaries. |
| Quantity | Nonnegative whole number of units. |
| Price | Nonnegative unit price in the source dataset’s units. The UI displays two decimal places. |
| Supplier | Optional supplier name. |
| Status | Computed from quantity on every read and write. |

Quantity 0 is **Out of Stock**, 1–5 is **Low Stock**, and 6 or more is **In Stock**. The attention queue sorts by quantity and then name. Stock-health chart slices count products. Category bars count units. Keyboard at 5 and Router at 6 demonstrate the low-stock boundary.

## Persistence

The supplied seed wraps each entire row, including the header, in quotes. The reader first parses a normal CSV record. When it gets a single field, it parses that field again. This preserves ordinary quoted fields and fields containing commas. A read never rewrites the file. Status is derived even when a stored label is stale.

An explicit save writes a standard seven-column CSV to a temporary file and then replaces the original. Mutations are serialized between sessions within one Streamlit process. This project is designed for one local app process. Test changes on a copy of the project or data file.

## Screen behavior

- **Dashboard** displays counts, a sorted list of products that need attention, a stock-health ring and units by category. Each queue action opens its own product. Clicking an alert card sets the matching filter.
- **Inventory** combines name search with category and status filters. Select a product to edit quantity/price or request deletion. Results are paged in sets of 20. On small screens, the table scrolls horizontally inside its panel.
- **Stock Alerts** switches between zero and low quantities. A restocked product leaves the filter when it no longer matches. The confirmation reports its new quantity and status.
- **Inventory Assistant** accepts a question or a clickable example. Supported questions include totals, low/out-of-stock lists, categories, suppliers and product lookup. It computes answers locally from the current inventory.
- **Product forms** retain values through validation, preview the stock status when quantity changes, and require a separate confirmation for deletion. Cancel returns to the previous screen.

See README.md for Windows setup, the launch command and the 5-to-6-unit demo.

## Repeatable checks

Run the included regression tests from the project root. They create temporary CSV files for mixed quoting, stock boundaries and a persisted restock with an assistant lookup.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
