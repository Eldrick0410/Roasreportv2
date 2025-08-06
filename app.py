import streamlit as st
import pandas as pd

st.title("📊 ROAS Metrics Generator with Product Name Mapping")

# --- File Uploaders ---
file1 = st.file_uploader("Upload File 1 (Product ID + Cost)", type=["xlsx"])
file2 = st.file_uploader("Upload File 2 (Creative Level Data)", type=["xlsx"])
file3 = st.file_uploader("Optional: Upload Product Name Mapping (Product ID + Product Name)", type=["xlsx"])

if file1 and file2:
    try:
        # --- Read Files ---
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        # Standardize column names
        df1.columns = df1.columns.str.strip().str.lower()
        df2.columns = df2.columns.str.strip().str.lower()

        # Dynamically detect "orders" column
        order_col = None
        for col in df2.columns:
            if "order" in col and "sku" in col:
                order_col = col
                break

        if not order_col:
            st.error("❌ Could not find a column containing both 'order' and 'sku' in File 2.")
        else:
            # Required columns
            required_file1_cols = {"product id", "cost"}
            required_file2_cols = {"product id", "product ad impressions", "product ad clicks", order_col, "gross revenue"}

            # Validate files
            if not required_file1_cols.issubset(df1.columns):
                st.error(f"❌ File 1 missing columns: {required_file1_cols - set(df1.columns)}")
            elif not {"product id", "product ad impressions", "product ad clicks", "gross revenue"}.issubset(df2.columns):
                st.error(f"❌ File 2 missing required columns except orders column.")
            else:
                # --- Aggregate File 2 ---
                df2_grouped = df2.groupby("product id", as_index=False).agg({
                    "product ad impressions": "sum",
                    "product ad clicks": "sum",
                    order_col: "sum",
                    "gross revenue": "sum"
                })

                # --- Merge with Cost Data ---
                merged = pd.merge(df1, df2_grouped, on="product id", how="left")
                merged.fillna(0, inplace=True)

                # --- Calculate Metrics ---
                merged["CPM"] = merged["cost"] / merged["product ad impressions"].replace(0, 1) * 1000
                merged["CPC"] = merged["cost"] / merged["product ad clicks"].replace(0, 1)
                merged["CTR"] = merged["product ad clicks"] / merged["product ad impressions"].replace(0, 1)
                merged["CR"] = merged[order_col] / merged["product ad clicks"].replace(0, 1)
                merged["ROAS"] = merged["gross revenue"] / merged["cost"].replace(0, 1)
                merged["CPP"] = merged["cost"] / merged[order_col].replace(0, 1)

                # --- Optional Product Name Merge ---
                if file3:
                    df3 = pd.read_excel(file3)
                    df3.columns = df3.columns.str.strip().str.lower()
                    if {"product id", "product name"}.issubset(df3.columns):
                        merged = pd.merge(df3, merged, on="product id", how="right")
                    else:
                        st.warning("⚠️ Product name file does not have both 'Product ID' and 'Product Name' columns. Skipping merge.")

                # --- Reorder Columns ---
                final_cols = ["product id"]
                if file3:
                    final_cols.append("product name")
                final_cols += [
                    "cost", "product ad impressions", "product ad clicks", order_col,
                    "gross revenue", "CPM", "CPC", "CTR", "CR", "ROAS", "CPP"
                ]
                merged = merged[final_cols]

                # --- Round Decimals ---
                merged[["CPM", "CPC", "ROAS", "CPP"]] = merged[["CPM", "CPC", "ROAS", "CPP"]].round(2)
                merged[["CTR", "CR"]] = merged[["CTR", "CR"]].round(4)

                # --- Display Table ---
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
