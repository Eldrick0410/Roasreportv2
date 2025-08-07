import streamlit as st
import pandas as pd

st.title("📊 ROAS Metrics Generator (Multi Cost Files + Creative Data)")

# Upload multiple cost files
cost_files = st.file_uploader("Upload Cost Files (Product ID + Cost)", type=["xlsx"], accept_multiple_files=True)

# Upload one creative file
creative_file = st.file_uploader("Upload Creative Level Data File", type=["xlsx"])

if cost_files and creative_file:
    try:
        # Load and combine all cost files
        cost_dfs = []
        for file in cost_files:
            df = pd.read_excel(file)
            df.columns = df.columns.str.strip().str.lower()
            cost_dfs.append(df)
        cost_df = pd.concat(cost_dfs, ignore_index=True)

        # Auto-detect cost file columns
        product_id_col_f1 = [c for c in cost_df.columns if "product" in c and "id" in c][0]
        cost_col = [c for c in cost_df.columns if "cost" in c][0]

        # Load creative data
        creative_df = pd.read_excel(creative_file)
        creative_df.columns = creative_df.columns.str.strip().str.lower()

        # Auto-detect creative columns
        product_id_col_f2 = [c for c in creative_df.columns if "product" in c and "id" in c][0]
        impressions_col = [c for c in creative_df.columns if "impression" in c][0]
        clicks_col = [c for c in creative_df.columns if "click" in c][0]
        orders_col = [c for c in creative_df.columns if "order" in c and "sku" in c][0]
        gmv_col = [c for c in creative_df.columns if "gross" in c or "revenue" in c][0]

        # Aggregate creative data
        creative_grouped = creative_df.groupby(product_id_col_f2, as_index=False).agg({
            impressions_col: "sum",
            clicks_col: "sum",
            orders_col: "sum",
            gmv_col: "sum"
        })

        # Merge all
        merged = pd.merge(cost_df[[product_id_col_f1, cost_col]], creative_grouped,
                          left_on=product_id_col_f1, right_on=product_id_col_f2, how="left")
        merged.fillna(0, inplace=True)

        # Rename for simplicity
        merged.rename(columns={
            product_id_col_f1: "Product ID",
            cost_col: "Cost",
            impressions_col: "Impressions",
            clicks_col: "Clicks",
            orders_col: "Orders",
            gmv_col: "Gross Revenue"
        }, inplace=True)

        # Metrics
        merged["CPM"] = merged["Cost"] / merged["Impressions"].replace(0, 1) * 1000
        merged["CPC"] = merged["Cost"] / merged["Clicks"].replace(0, 1)
        merged["CTR"] = merged["Clicks"] / merged["Impressions"].replace(0, 1)
        merged["CR"] = merged["Orders"] / merged["Clicks"].replace(0, 1)
        merged["ROAS"] = merged["Gross Revenue"] / merged["Cost"].replace(0, 1)
        merged["CPP"] = merged["Cost"] / merged["Orders"].replace(0, 1)

        # Round
        merged = merged.round(2)

        # Show result
        st.success("✅ Metrics calculated successfully!")
        st.dataframe(merged)

        # Download
        csv = merged.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download ROAS Report",
            data=csv,
            file_name="ROAS_Report.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
