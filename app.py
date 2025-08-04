import streamlit as st
import pandas as pd

st.title("📊 ROAS Metrics Generator (Decimals Only)")

# Upload two Excel files
file1 = st.file_uploader("Upload File 1 (Product ID + Cost)", type=["xlsx"])
file2 = st.file_uploader("Upload File 2 (Creative Level Data)", type=["xlsx"])

if file1 and file2:
    try:
        # Read the data
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        # Standardize column names
        df1.columns = df1.columns.str.strip().str.lower()
        df2.columns = df2.columns.str.strip().str.lower()

        # Required columns
        required_file1_cols = {"product id", "cost"}
        required_file2_cols = {
            "product id", 
            "product ad impressions", 
            "product ad clicks", 
            "orders (sku)", 
            "gross revenue"
        }

        # Validate files
        if not required_file1_cols.issubset(df1.columns):
            st.error(f"❌ File 1 missing columns: {required_file1_cols - set(df1.columns)}")
        elif not required_file2_cols.issubset(df2.columns):
            st.error(f"❌ File 2 missing columns: {required_file2_cols - set(df2.columns)}")
        else:
            # Aggregate File 2
            df2_grouped = df2.groupby("product id", as_index=False).agg({
                "product ad impressions": "sum",
                "product ad clicks": "sum",
                "orders (sku)": "sum",
                "gross revenue": "sum"
            })

            # Merge
            merged = pd.merge(df1, df2_grouped, on="product id", how="left")
            merged.fillna(0, inplace=True)

            # Calculate metrics (CTR & CR in decimal form)
            merged["CPM"] = merged["cost"] / merged["product ad impressions"].replace(0, 1) * 1000
            merged["CPC"] = merged["cost"] / merged["product ad clicks"].replace(0, 1)
            merged["CTR"] = merged["product ad clicks"] / merged["product ad impressions"].replace(0, 1)
            merged["CR"] = merged["orders (sku)"] / merged["product ad clicks"].replace(0, 1)
            merged["ROAS"] = merged["gross revenue"] / merged["cost"].replace(0, 1)
            merged["CPP"] = merged["cost"] / merged["orders (sku)"].replace(0, 1)

            # Reorder & round decimals
            final_cols = [
                "product id", "cost", "product ad impressions", "product ad clicks",
                "orders (sku)", "gross revenue", "CPM", "CPC", "CTR", "CR", "ROAS", "CPP"
            ]
            merged = merged[final_cols]
            merged[["CTR", "CR", "ROAS"]] = merged[["CTR", "CR", "ROAS"]].round(4)

            # Show dataframe
            st.success("✅ Metrics calculated successfully!")
            st.dataframe(merged)

            # Download CSV (decimals only)
            csv = merged.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download ROAS Report (Decimals
