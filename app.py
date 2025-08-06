import streamlit as st
import pandas as pd

st.title("📊 ROAS Metrics Generator with Product Name (Optional)")

# Upload files
file1 = st.file_uploader("Upload File 1 (Product ID + Cost)", type=["xlsx"])
file2 = st.file_uploader("Upload File 2 (Creative Level Data)", type=["xlsx"])
file3 = st.file_uploader("Optional: Upload Product Name Mapping (Product ID + Product Name)", type=["xlsx"])

if file1 and file2:
    try:
        # Read the data
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        # Normalize column names
        df1.columns = df1.columns.str.strip().str.lower()
        df2.columns = df2.columns.str.strip().str.lower()

        # Try to detect "orders" column automatically
        orders_col = next((col for col in df2.columns if "order" in col and "sku" in col.lower()), None)
        revenue_col = next((col for col in df2.columns if "gross" in col and "revenue" in col.lower()), None)
        impressions_col = next((col for col in df2.columns if "impression" in col), None)
        clicks_col = next((col for col in df2.columns if "click" in col), None)

        if not all([orders_col, revenue_col, impressions_col, clicks_col]):
            st.error("❌ Could not auto-detect one of the required columns (Orders, Revenue, Impressions, Clicks).")
        else:
            # Aggregate File 2
            df2_grouped = df2.groupby("product id", as_index=False).agg({
                impressions_col: "sum",
                clicks_col: "sum",
                orders_col: "sum",
                revenue_col: "sum"
            })

            # Merge
            merged = pd.merge(df1, df2_grouped, on="product id", how="left")
            merged.fillna(0, inplace=True)

            # Calculate metrics
            merged["CPM"] = merged["cost"] / merged[impressions_col].replace(0, 1) * 1000
            merged["CPC"] = merged["cost"] / merged[clicks_col].replace(0, 1)
            merged["CTR"] = merged[clicks_col] / merged[impressions_col].replace(0, 1)
            merged["CR"] = merged[orders_col] / merged[clicks_col].replace(0, 1)
            merged["ROAS"] = merged[revenue_col] / merged["cost"].replace(0, 1)
            merged["CPP"] = merged["cost"] / merged[orders_col].replace(0, 1)

            # Merge product name if File 3 is uploaded
            if file3:
                df3 = pd.read_excel(file3)
                df3.columns = df3.columns.str.strip().str.lower()
                if {"product id", "product name"}.issubset(df3.columns):
                    merged = pd.merge(df3, merged, on="product id", how="right")

            # Round decimals
            merged = merged.round(2)

            # Show dataframe
            st.success("✅ Metrics calculated successfully!")
            st.dataframe(merged)

            # Download CSV (decimals only)
            csv = merged.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download ROAS Report (with Product Name if available)",
                data=csv,
                file_name="ROAS_Report.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
