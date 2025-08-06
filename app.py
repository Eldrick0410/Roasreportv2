import streamlit as st
import pandas as pd

st.title("📊 ROAS Metrics Generator (Auto Column Detection + Product Name Mapping)")

# File uploads
file1 = st.file_uploader("Upload File 1 (Product ID + Cost)", type=["xlsx"])
file2 = st.file_uploader("Upload File 2 (Creative Level Data)", type=["xlsx"])
file3 = st.file_uploader("Optional: Upload Product Name Mapping (Product ID + Product Name)", type=["xlsx"])

if file1 and file2:
    try:
        # --- Read files ---
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        # Clean column names
        df1.columns = df1.columns.str.strip().str.lower()
        df2.columns = df2.columns.str.strip().str.lower()

        # Auto-detect columns in File 1
        product_id_col_f1 = [c for c in df1.columns if "product" in c and "id" in c][0]
        cost_col = [c for c in df1.columns if "cost" in c][0]

        # Auto-detect columns in File 2
        product_id_col_f2 = [c for c in df2.columns if "product" in c and "id" in c][0]
        impressions_col = [c for c in df2.columns if "impression" in c][0]
        clicks_col = [c for c in df2.columns if "click" in c][0]
        orders_col = [c for c in df2.columns if "order" in c and "sku" in c][0]
        gmv_col = [c for c in df2.columns if "gross" in c or "revenue" in c][0]

        # Aggregate File 2
        df2_grouped = df2.groupby(product_id_col_f2, as_index=False).agg({
            impressions_col: "sum",
            clicks_col: "sum",
            orders_col: "sum",
            gmv_col: "sum"
        })

        # Merge File 1 + File 2
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

        # --- Calculate Metrics ---
        merged["CPM"] = merged["Cost"] / merged["Impressions"].replace(0, 1) * 1000
        merged["CPC"] = merged["Cost"] / merged["Clicks"].replace(0, 1)
        merged["CTR"] = merged["Clicks"] / merged["Impressions"].replace(0, 1)
        merged["CR"] = merged["Orders"] / merged["Clicks"].replace(0, 1)
        merged["ROAS"] = merged["Gross Revenue"] / merged["Cost"].replace(0, 1)
        merged["CPP"] = merged["Cost"] / merged["Orders"].replace(0, 1)

        # --- Optional Product Name Merge ---
        if file3:
            df3 = pd.read_excel(file3)
            df3.columns = df3.columns.str.strip().str.lower()
            if {"product id", "product name"}.issubset(df3.columns):
                merged = pd.merge(df3, merged, left_on="product id", right_on="Product ID", how="right")
                merged.drop(columns=["product id"], inplace=True)  # remove duplicate key column
            else:
                st.warning("⚠️ Product name file does not have both 'Product ID' and 'Product Name' columns. Skipping merge.")

        # --- Round Decimals ---
        merged[["CPM", "CPC", "ROAS", "CPP"]] = merged[["CPM", "CPC", "ROAS", "CPP"]].round(2)
        merged[["CTR", "CR"]] = merged[["CTR", "CR"]].round(4)

        # Display table
        st.success("✅ Metrics calculated successfully!")
        st.dataframe(merged)

        # --- Download CSV ---
        csv = merged.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download ROAS Report",
            data=csv,
            file_name="ROAS_Report.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
