"""Small presentation helpers shared by the dashboard and the other screens."""

from base64 import b64encode
from html import escape

import streamlit as st


def esc(value):
    return escape(str(value), quote=True)


# Each icon uses the same 24 x 24 grid and rounded strokes.
PATHS = {
    "box": '<path d="m3 7 9-5 9 5v10l-9 5-9-5zM3 7l9 5 9-5M12 12v10M7.5 4.5l9 5v4"/>',
    "layers": '<path d="m2 7 10-5 10 5-10 5zM2 12l10 5 10-5M2 17l10 5 10-5"/>',
    "alert": '<path d="m10.3 4.2-8 14A1.9 1.9 0 0 0 4 21h16a1.9 1.9 0 0 0 1.7-2.8l-8-14a1.9 1.9 0 0 0-3.4 0zM12 9v5M12 17h.01"/>',
    "empty": '<path d="m3 7 9-5 9 5-9 5zM3 7v10l9 5 9-5V7M12 12v10M16 13h3"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "list": '<path d="M9 6h12M9 12h12M9 18h12M3 6h1M3 12h1M3 18h1"/>',
    "chat": '<path d="M3 4h18v13H8l-5 4zM8 9h8M8 12h5"/>',
    "arrow": '<path d="M6 18 18 6M7 6h11v11"/>',
    "check": '<path d="m4 12 5 5L20 6"/>',
    "search": '<circle cx="10.4" cy="10.4" r="6.5"/><path d="m15.2 15.2 5.3 5.3"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 4 16 4 16 0V5M4 12v7c0 4 16 4 16 0v-7"/>',
    "monitor": '<rect x="2.5" y="3.5" width="19" height="13" rx="2"/><path d="M12 17v4m-4 0h8"/>',
    "keyboard": '<rect x="1.5" y="5" width="21" height="14" rx="2"/><path d="M5 9h1m3 0h1m3 0h1m3 0h1M5 12h1m3 0h1m3 0h1m3 0h1M8 15h8"/>',
    "headphones": '<path d="M3 15v-2a9 9 0 0 1 18 0v2"/><rect x="3" y="12" width="4.5" height="8" rx="1.8"/><rect x="16.5" y="12" width="4.5" height="8" rx="1.8"/>',
    "printer": '<path d="M6 8V3h12v5M6 17H3V8h18v9h-3M6 14h12v7H6zM17 11h1"/>',
    "desk": '<path d="M2 9h20v3H2zM4 12v9m16-9v9m-8-9v5h8"/>',
    "webcam": '<circle cx="12" cy="9" r="6.5"/><circle cx="12" cy="9" r="2.2"/><path d="M12 16v3m-6 2 2-2h8l2 2z"/>',
    "pencil": '<path d="m3 21 5-1L21 7l-4-4L4 16zM14 6l4 4"/>',
}
PATHS["stack"] = PATHS["layers"]
PATHS["inventory"] = PATHS["box"]


def svg_image(svg, size=None):
    """Use an image because Streamlit sanitizes inline SVG elements in HTML."""
    encoded = b64encode(svg.encode("utf-8")).decode("ascii")
    dimensions = f' width="{size}" height="{size}"' if size else ''
    return f'<img alt="" aria-hidden="true"{dimensions} src="data:image/svg+xml;base64,{encoded}">'


def icon(name, size=20, color="#2C5360"):
    path = PATHS.get(name, PATHS["box"])
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
           f'stroke="{color}" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">{path}</svg>')
    return svg_image(svg, size)


STATUS_CLASS = {"In Stock": "in", "Low Stock": "low", "Out of Stock": "out"}


def status_badge(status):
    tone = STATUS_CLASS.get(status, "neutral")
    return f'<span class="stock-badge {tone}"><i></i>{esc(status)}</span>'


def open_product(action, product_id=None):
    st.session_state.product_action = action
    st.session_state.product_id = product_id


def attention_rows(data, key_prefix):
    for index, row in enumerate(data.itertuples(index=False)):
        label = str(row.Product_Name).casefold()
        glyph = label if label in PATHS else {
            "Electronics": "monitor", "Furniture": "desk", "Stationery": "pencil"
        }.get(row.Category, "box")
        tone = {"Electronics": "sky", "Office Equipment": "sand", "Furniture": "rose",
                "Accessories": "lilac"}.get(row.Category, "mint")
        with st.container(key=f"{key_prefix}_stockrow_{index}"):
            detail, action = st.columns([4, 1.35], vertical_alignment="center")
            with detail:
                st.html(
                    f'<div class="stock-row"><span class="product-tile {tone}">{icon(glyph, 23)}</span>'
                    f'<div class="product-text"><b>{esc(row.Product_Name)}</b>'
                    f'<small>{esc(row.Product_ID)} <span>·</span> {row.Quantity:,} '
                    f'{"unit" if row.Quantity == 1 else "units"}</small></div>'
                    f'{status_badge(row.Status)}</div>'
                )
            with action:
                st.button("Update stock", key=f"{key_prefix}_update_{index}",
                          help=f"Update stock for {row.Product_Name} ({row.Product_ID})",
                          on_click=open_product, args=("edit", row.Product_ID))
