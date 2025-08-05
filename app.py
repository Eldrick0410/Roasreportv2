import streamlit as st
import pandas as pd

st.title("📊 ROAS Metrics Generator (Auto Column Detection)")

# Upload files
file1 = st.file_uploader("Upload File 1 (Product ID + Cost)", type=["xlsx"])
file2 = st.file_uploader("Upload File 2 (Creative Level Data)", type=["xlsx"])

def find_col(df, keywords):
    """Find first column that contains all keywords."""
    for col in df.columns:
        if all(k in col for k in keywords):
            return col
    return None

if file1 and file2:
    try:
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        # Normalize columns
        df1.columns = df1.columns.str.strip().str.lower()
        df2.columns = df2.columns.str.strip().str.lower()

        # Auto-detect columns
        col_product_id_1 = find_col(df1, ["product", "id"])
        col_cost = find_col(df1, ["cost"])
        col_product_id_2 = find_col(df2, ["product", "id"])
        col_impressions = find_col(df2, ["impression"])
        col_clicks = find_col(df2, ["click"])
        col_orders = find_col(df2, ["order", "sku"])  # Flexible detection
        col_revenue = find_col(df2, ["gross", "revenue"])

        detected = {
            "Product ID (File1)": col_product_id_1,
            "Cost": col_cost,
            "Product ID (File2)": col_product_id_2,
            "Impressions": col_impressions,
            "Clicks": col_clicks,
            "Orders": col_orders,
            "Gross Revenue": col_revenue
        }
        st.write("### 🔍 Detected Columns")
        st.json(detected)

        # Stop if any column is missing
        if None in detected.values():
            st.error("❌ Could not detect all required columns. Check file headers.")
            st.stop()

        # Aggregate File2
        df2_grouped = df2.groupby(col_product_id_2, as_index=False).agg({
            col_impressions: "sum",
            col_clicks: "sum",
            col_orders: "sum",
            col_revenue: "sum"
        })

        # Merge and fill missing
        merged = pd.merge(df1, df2_grouped, left_on=col_product_id_1, right_on=col_product_id_2, how="left")
        merged.fillna(0, inplace=True)

        # Calculate metrics
        merged["CPM"] = merged[col_cost] / merged[col_impressions].replace(0, 1) * 1000
        merged["CPC"] = merged[col_cost] / merged[col_clicks].replace(0, 1)
        merged["CTR"] = merged[col_clicks] / merged[col_impressions].replace(0, 1)
        merged["CR"] = merged[col_orders] / merged[col_clicks].replace(0, 1)
        merged["ROAS"] = merged[col_revenue] / merged[col_cost].replace(0, 1)
        merged["CPP"] = merged[col_cost] / merged[col_orders].replace(0, 1)

        # Reorder & round
        merged_final = merged[[col_product_id_1, col_cost, col_impressions, col_clicks, col_orders, col_revenue,
                               "CPM", "CPC", "CTR", "CR", "ROAS", "CPP"]].copy()
        for col in ["CPM", "CPC", "ROAS", "CPP"]:
            merged_final[col] = merged_final[col].round(2)
        merged_final[["CTR", "CR"]] = merged_final[["CTR", "CR"]].round(4)

        # Show dataframe
        st.success("✅ Metrics calculated successfully!")
        st.dataframe(merged_final)

        # Download CSV
        csv = merged_final.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download ROAS Report (Decimals Only)",
            data=csv,
            file_name="ROAS_Report.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
