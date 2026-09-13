"""Demand forecasting and product-ranking workspace."""

from __future__ import annotations

from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st

from modules.calendar_utils import convert_gregorian_to_hijri_string, get_next_week_dates
from modules.data_loader import load_raw_data, standardize_sales_data
from modules.forecaster import predict_next_week_sales


def sample_dataset() -> pd.DataFrame:
    """Create a small, realistic dataset so the workflow is instantly explorable."""
    products = [
        ("SKU-100", "Classic Cotton Tee", "Apparel", 38, 115),
        ("SKU-200", "Insulated Travel Mug", "Home & Lifestyle", 22, 54),
        ("SKU-300", "Wireless Earbuds", "Electronics", 16, 31),
        ("SKU-400", "Date Gift Box", "Grocery", 44, 86),
        ("SKU-500", "Running Shoes", "Apparel", 12, 21),
    ]
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=28)
    rows = []
    for product_id, name, category, base_sales, stock in products:
        for offset, sale_date in enumerate(dates):
            rows.append({
                "date": sale_date,
                "product_id": product_id,
                "product_name": name,
                "category": category,
                "units_sold": max(0, base_sales + ((offset * 3 + len(product_id)) % 11) - 5),
                "stock_on_hand": stock,
            })
    return pd.DataFrame(rows)


def excel_export(data: pd.DataFrame) -> bytes:
    """Create an in-memory Excel download without writing user data to disk."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        data.to_excel(writer, index=False, sheet_name="Demand Forecast")
    return buffer.getvalue()


st.title("Demand Forecasting & Sales Ranking")
st.caption("Upload daily sales history, factor in next week's calendar, and turn demand into replenishment actions.")

with st.sidebar:
    st.header("Forecast data")
    uploaded_file = st.file_uploader("Upload sales data", type=["csv", "xlsx", "xls", "db"])
    if st.button("Load Sample Dataset", use_container_width=True):
        st.session_state["forecast_source"] = sample_dataset()
        st.session_state["uploaded_file_id"] = "sample"
        st.session_state.pop("processing_report", None)
        st.session_state.pop("forecast_results", None)
    st.caption("Supported: CSV, Excel, and SQLite database exports.")

upload_id = (getattr(uploaded_file, "name", ""), getattr(uploaded_file, "size", 0)) if uploaded_file else None
if uploaded_file is not None and st.session_state.get("uploaded_file_id") != upload_id:
    try:
        raw_data = load_raw_data(uploaded_file)
        clean_data, processing_report = standardize_sales_data(raw_data)
        st.session_state["forecast_source"] = clean_data
        st.session_state["processing_report"] = processing_report
        st.session_state["uploaded_file_id"] = upload_id
        st.session_state.pop("forecast_results", None)
    except (ValueError, TypeError) as exc:
        st.error(f"Could not process the upload: {exc}")

next_week = get_next_week_dates()
st.subheader("Next-week planning calendar")
calendar_preview = pd.DataFrame({
    "Gregorian date": next_week.strftime("%a, %d %b %Y"),
    "Hijri date": [convert_gregorian_to_hijri_string(value) for value in next_week],
})
st.dataframe(calendar_preview, use_container_width=True, hide_index=True)

source_data = st.session_state.get("forecast_source")
if source_data is None:
    st.info("Upload a sales export in the sidebar or load the sample dataset to begin.")
    st.stop()

report = st.session_state.get("processing_report")
if report:
    if report["status"] == "success_with_warnings":
        st.warning("Data standardized with notes: " + "; ".join(report["warnings"] or report["defaults_applied"]))
    else:
        st.success(f"Loaded and standardized {report['output_rows']:,} data rows.")

with st.expander("Preview input data", expanded=False):
    st.dataframe(source_data.head(25), use_container_width=True, hide_index=True)

if st.button("Run next-week predictions", type="primary"):
    try:
        with st.spinner("Forecasting demand and checking inventory coverage..."):
            st.session_state["forecast_results"] = predict_next_week_sales(source_data)
    except (ValueError, TypeError, RuntimeError) as exc:
        st.error(f"Predictions could not be completed: {exc}")

results = st.session_state.get("forecast_results")
if results is None:
    st.stop()
if results.empty:
    st.warning("No usable sales rows were found for forecasting.")
    st.stop()

category_totals = results.groupby("category", dropna=False)["predicted_units_next_week"].sum()
top_category = category_totals.idxmax()
total_expected = int(results["predicted_units_next_week"].sum())
stockout_risks = int(results["reorder_recommended"].sum())
kpi_one, kpi_two, kpi_three = st.columns(3)
kpi_one.metric("Total Expected Sales", f"{total_expected:,} units")
kpi_two.metric("Top Predicted Category", str(top_category), f"{int(category_totals.max()):,} units")
kpi_three.metric("High Stockout Risk Items", stockout_risks)

st.subheader("Top 10 predicted best sellers")
top_ten = results.nlargest(10, "predicted_units_next_week")
chart = px.bar(
    top_ten.sort_values("predicted_units_next_week"),
    x="predicted_units_next_week",
    y="product_name",
    color="category",
    orientation="h",
    text="predicted_units_next_week",
    labels={"predicted_units_next_week": "Predicted units next week", "product_name": "Product"},
)
chart.update_layout(height=430, legend_title_text="Category", margin=dict(l=0, r=0, t=25, b=0))
chart.update_traces(textposition="outside", cliponaxis=False)
st.plotly_chart(chart, use_container_width=True)

st.subheader("Reorder-ready sales ranking")
search_term = st.text_input("Search products, categories, or IDs", placeholder="e.g. SKU-100 or Apparel")
if search_term:
    searchable = results.astype(str).apply(lambda column: column.str.contains(search_term, case=False, na=False))
    filtered_results = results[searchable.any(axis=1)]
else:
    filtered_results = results
st.dataframe(filtered_results, use_container_width=True, hide_index=True)

download_csv, download_excel, _ = st.columns([1, 1, 2])
with download_csv:
    st.download_button(
        "Export CSV",
        data=filtered_results.to_csv(index=False).encode("utf-8"),
        file_name="smartstock_demand_forecast.csv",
        mime="text/csv",
        use_container_width=True,
    )
with download_excel:
    st.download_button(
        "Export Excel",
        data=excel_export(filtered_results),
        file_name="smartstock_demand_forecast.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
