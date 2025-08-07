import streamlit as st
import pandas as pd

st.title("📊 ROAS Metrics Generator (Multi-File Creative Upload)")

# Upload base file
base_file = st.file_uploader("Upload Base File (Product ID + Cost)", type=["xlsx"])

# Upload multiple creative data files
creative_files = st.file_uploader("Upload Creative-Level File(s)", type=["xlsx"], accept_multiple_files=True)

if base_file and creative_files:
    try:
        # Read base file
        df_base = pd.read_excel(base_file)
        df_base.columns = df_base.columns.str.strip().str.lower()

        # Auto-detect base file columns
        product_id_col_base = [c for c in df_base.columns if "product" in c and "id" in c][0]
        cost_col = [c for c in df_base.columns if "cost" in c][0]

        # Combine creative files
        creative_dfs = []
        for file in creative_files:
            df = pd.read_excel(file)
            df.columns = df.columns.str.strip().str.lower()
            creative_dfs.append(df)

        df_creative = pd.concat(creative_dfs, ignore_index=True)

        # Auto-detect creative file columns
        product_id_col_creative = [c for c in df_creative.columns if "product" in c and "id" in c][0]
        impressions_col = [c for c in df_creative.columns if "impression" in c][0]
        clicks_col = [c for c in df_creative.columns if "click" in c][0]
        orders_col = [c for c in df_creative.columns if "order" in c and "sku" in c][0]
        gmv_col = [c for c in df_creative.columns if "gross" in c or "revenue" in c][0]

        # Aggregate creative data
        df_creative_grouped = df_creative.groupby(product_id_col_creative, as_index=False).agg({
            impressions_col: "sum",
            clicks_col: "sum",
            orders_col: "sum",
            gmv_col: "sum"
        })

        # Merge with base file
        merged = pd.merge(
            df_base[[product_id_col_base, cost_col]],
            df_creative_grouped,
            left_on=product_id_col_base,
            right_on=product_id_col_creative,
            how="left"
        ).fillna(0)

        # Rename columns
        merged.rename(columns={
            product_id_col_base: "Product ID",
            cost_col: "Cost",
            impressions_col: "Impressions",
            clicks_col: "Clicks",
            orders_col: "Orders",
            gmv_col: "GMV"
        }, inplace=True)

        # Metrics
        merged["CPM"] = merged["Cost"] / merged["Impressions"].replace(0, 1) * 1000
        merged["CPC"] = merged["Cost"] / merged["Clicks"].replace(0, 1)
        merged["CTR"] = merged["Clicks"] / merged["Impressions"].replace(0, 1)
        merged["CR"] = merged["Orders"] / merged["Clicks"].replace(0, 1)
        merged["ROAS"] = merged["GMV"] / merged["Cost"].replace(0, 1)
        merged["CPP"] = merged["Cost"] / merged["Orders"].replace(0, 1)

        # Round
        merged = merged.round(2)

        # Show full table
        st.success("✅ Metrics calculated successfully!")
        st.dataframe(merged)

        # Monthly Summary
        summary = {
            "Spend": merged["Cost"].sum(),
            "Orders": merged["Orders"].sum(),
            "GMV": merged["GMV"].sum(),
        }
        summary["ROAS"] = summary["GMV"] / summary["Spend"] if summary["Spend"] != 0 else 0
        summary["CTR"] = merged["Clicks"].sum() / merged["Impressions"].sum() if merged["Impressions"].sum() != 0 else 0
        summary["CR"] = merged["Orders"].sum() / merged["Clicks"].sum() if merged["Clicks"].sum() != 0 else 0

        summary_df = pd.DataFrame([summary]).round(2)
        st.subheader("📈 Monthly Summary")
        st.dataframe(summary_df)

        # Download CSV
        csv = merged.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download ROAS Report",
            data=csv,
            file_name="ROAS_Report.csv",
            mime="text/csv"
        )

    except Exception as e:
        st.error(f"❌ Error: {e}")
