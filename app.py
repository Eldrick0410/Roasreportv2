import streamlit as st
import pandas as pd

st.title("📊 ROAS Metrics Generator (Auto Column Detection)")

# File uploads
file1 = st.file_uploader("Upload File 1 (Product ID + Cost)", type=["xlsx"])
file2 = st.file_uploader("Upload File 2 (Creative Level Data)", type=["xlsx"])

if file1 and file2:
    try:
        # Read files
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        # Clean column names
        df1.columns = df1.columns.str.strip().str.lower()
        df2.columns = df2.columns.str.strip().str.lower()

        # Auto-detect columns
        product_id_col_f1 = [c for c in df1.columns if "product" in c and "id" in c][0]
        cost_col = [c for c in df1.columns if "cost" in c][0]

        product_id_col_f2 = [c for c in df2.columns if "product" in c and "id" in c][0]
        impressions_col = [c for c in df2.columns if "impression" in c][0]
        clicks_col = [c for c in df2.columns if "click" in c][0]
        orders_col = [c for c in df2.columns if "order" in c and "sku" in c][0]
        gmv_col = [c for c in df2.columns if "gross" in c or "revenue" in c][0]

        # Aggregate file 2
        df2_grouped = df2.groupby(product_id_col_f2, as_index=False).agg({
            impressions_col: "sum",
            clicks_col: "sum",
            orders_col: "sum",
            gmv_col: "sum"
        })

        # Merge
        merged = pd.merge(df1[[product_id_col_f1, cost_col]], df2_grouped,
                          left_on=product_id_col_f1, right_on=product_id_col_f2, how="left")
        merged.fillna(0, inplace=True)

        # Rename columns for easier reference
        merged.rename(columns={
            product_id_col_f1: "Product ID",
            cost_col: "Cost",
            impressions_col: "Impressions",
            clicks_col: "Clicks",
            orders_col: "Orders",
            gmv_col: "Gross Revenue"
        }, inplace=True)

        # Calculate metrics
        merged["CPM"] = merged["Cost"] / merged["Impressions"].replace(0, 1) * 1000
        merged["CPC"] = merged["Cost"] / merged["Clicks"].replace(0, 1)
        merged["CTR"] = merged["Clicks"] / merged["Impressions"].replace(0, 1)
        merged["CR"] = merged["Orders"] / merged["Clicks"].replace(0, 1)
        merged["ROAS"] = merged["Gross Revenue"] / merged["Cost"].replace(0, 1)
        merged["CPP"] = merged["Cost"] / merged["Orders"].replace(0, 1)

        # Round decimals to 2 places
        merged = merged.round(2)

        # Display table
        st.success("✅ Metrics calculated successfully!")
        st.dataframe(merged)

        # Download CSV
        csv = merged.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download ROAS Report (Decimals Only)",
            data=csv,
            file_name="ROAS_Report.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
