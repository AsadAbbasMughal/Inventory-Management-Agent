# Inventory Management Agent

A local Streamlit app for checking stock, updating products and asking inventory questions. It runs with Python 3.12 and stores inventory in the existing seven-column CSV.

## Run on Windows

Extract the ZIP. In PowerShell, open the folder containing **this README, app.py and .streamlit**. Create the virtual environment once on your computer. If you keep an existing environment, use its interpreter for the installation step.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run the app from the same folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Open http://127.0.0.1:8501 in your browser. Press Ctrl+C in the terminal to stop. Dependencies are installed once. The app and its visuals run locally.

## One-minute class demo

Use a copy of the extracted project if you want to keep the original stock levels for another presentation.

1. Open **Dashboard** and point out the distinction between 15 products and 290 units.
2. Select **Low stock**, then **Update stock** beside **Keyboard (P003)**.
3. Change Quantity from **5** to **6**. Press Tab to see its new status, then choose **Save changes**.
4. Keyboard leaves the Low Stock list. The dashboard now shows **3** low-stock products and **291** total units.
5. In **Inventory Assistant**, enter **Keyboard**. It reports **6 units · In Stock**. Reload the page, ask again and the same answer comes from the CSV.

## Project guide

The root app.py is the entry point. The nested Inventory_Management_Agent directory is the original archived duplicate. Open PROJECT_DOCUMENTATION.md for a short walkthrough of the active code and data format.
