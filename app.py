import streamlit as st
import pandas as pd

st.title("📊 ROAS Metrics Generator (With CTR & CR in Decimals)")

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

        # Identify columns
        required_file1_cols = {"product id", "cost"}
        orders_col = None
        for col in df2.columns:
            if "order" in col or "sku" in col:
                orders_col = col
                break

        if not required_file1_cols.issubset(df1.columns):
            st.error(f"❌ File 1 missing columns: {required_file1_cols - set(df1.columns)}")
        elif not {"product id", "product ad impressions", "product ad clicks", "gross revenue"}.issubset(df2.columns):
            st.error("❌ File 2 must contain: Product ID, Product Ad Impressions, Product Ad Clicks, and Gross Revenue")
        elif not orders_col:
            st.error("❌ Could not detect any Orders/SKU column in File 2")
        else:
            # Aggregate File 2
            df2_grouped = df2.groupby("product id", as_index=False).agg({
                "product ad impressions": "sum",
                "product ad clicks": "sum",
                orders_col: "sum",
                "gross revenue": "sum"
            })

            # Merge
            merged = pd.merge(df1, df2_grouped, on="product id", how="left")
            merged.fillna(0, inplace=True)

            # Calculate metrics (all in decimals)
            merged["CPM"] = merged["cost"] / merged["product ad impressions"].replace(0, 1) * 1000
            merged["CPC"] = merged["cost"] / merged["product ad clicks"].replace(0, 1)
            merged["CTR"] = merged["product ad clicks"] / merged["product ad impressions"].replace(0, 1)
            merged["CR"] = merged[orders_col] / merged["product ad clicks"].replace(0, 1)
            merged["ROAS"] = merged["gross revenue"] / merged["cost"].replace(0, 1)
            merged["CPP"] = merged["cost"] / merged[orders_col].replace(0, 1)

            # Reorder & round to 2 decimals
            final_cols = [
                "product id", "cost", "product ad impressions", "product ad clicks",
                orders_col, "gross revenue", "CPM", "CPC", "CTR", "CR", "ROAS", "CPP"
            ]
            merged = merged[final_cols]
            merged = merged.round(2)

            # Show dataframe
            st.success(f"✅ Metrics calculated successfully! Using orders column: **{orders_col}**")
            st.dataframe(merged)

            # Monthly summary table
            summary = pd.DataFrame([{
                "Total Spend": merged["cost"].sum(),
                "Total Orders": merged[orders_col].sum(),
                "Total GMV": merged["gross revenue"].sum(),
                "ROAS": merged["gross revenue"].sum() / merged["cost"].sum() if merged["cost"].sum() != 0 else 0
            }]).round(2)

            st.subheader("📌 Monthly Performance Summary")
            st.dataframe(summary)

            # Download CSV (decimals only)
            csv = merged.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download ROAS Report (Decimals Only)",
                data=csv,
                file_name="ROAS_Report.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
