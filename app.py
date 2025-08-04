import streamlit as st
import pandas as pd

st.title("📊 ROAS Metrics Generator (With Monthly Summary)")

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

            # Show detailed table
            st.success("✅ Metrics calculated successfully!")
            st.dataframe(merged)

            # --- Monthly Summary Table ---
            total_cost = merged["cost"].sum()
            total_impressions = merged["product ad impressions"].sum()
            total_clicks = merged["product ad clicks"].sum()
            total_orders = merged["orders (sku)"].sum()
            total_gmv = merged["gross revenue"].sum()

            summary_data = {
                "Total Cost": [total_cost],
                "Total Impressions": [total_impressions],
                "Total Clicks": [total_clicks],
                "Total Orders": [total_orders],
                "Total GMV": [total_gmv],
                "CPM": [total_cost / total_impressions * 1000 if total_impressions else 0],
                "CPC": [total_cost / total_clicks if total_clicks else 0],
                "CTR": [total_clicks / total_impressions if total_impressions else 0],
                "CR": [total_orders / total_clicks if total_clicks else 0],
                "ROAS": [total_gmv / total_cost if total_cost else 0],
                "CPP": [total_cost / total_orders if total_orders else 0]
            }

            summary_df = pd.DataFrame(summary_data)
            summary_df[["CTR", "CR", "ROAS"]] = summary_df[["CTR", "CR", "ROAS"]].round(4)

            st.subheader("📈 Monthly Performance Summary")
            st.dataframe(summary_df)

            # --- Download CSV (decimals only) ---
            csv = merged.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download ROAS Report (Decimals Only)",
                data=csv,
                file_name="ROAS_Report.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")



