import streamlit as st
import pandas as pd

st.title("📊 ROAS Generator (Cost + Creative Files with Product Name in Cost File)")

# Upload files
cost_files = st.file_uploader("Upload Cost Files (Must include Product ID + Product Name + Cost)", type=["xlsx"], accept_multiple_files=True)
creative_file = st.file_uploader("Upload Creative-Level Data File", type=["xlsx"])

if cost_files and creative_file:
    try:
        # Combine cost files
        cost_dfs = []
        for file in cost_files:
            df = pd.read_excel(file)
            df.columns = df.columns.str.strip()
            cost_dfs.append(df)
        cost_df = pd.concat(cost_dfs, ignore_index=True)

        st.subheader("Step 1: Select Columns from Cost Files")
        st.write("Detected columns:", list(cost_df.columns))
        product_id_col = st.selectbox("Select Product ID column", cost_df.columns)
        product_name_col = st.selectbox("Select Product Name column", cost_df.columns)
        cost_col = st.selectbox("Select Cost column", cost_df.columns)

        # Upload creative file
        creative_df = pd.read_excel(creative_file)
        creative_df.columns = creative_df.columns.str.strip()

        st.subheader("Step 2: Select Columns from Creative File")
        st.write("Detected columns:", list(creative_df.columns))
        creative_id_col = st.selectbox("Select Product ID column from Creative File", creative_df.columns)
        impressions_col = st.selectbox("Select Impressions column", creative_df.columns)
        clicks_col = st.selectbox("Select Clicks column", creative_df.columns)
        orders_col = st.selectbox("Select Orders column", creative_df.columns)
        gmv_col = st.selectbox("Select Gross Revenue (GMV) column", creative_df.columns)

        # Group creative-level data
        creative_grouped = creative_df.groupby(creative_id_col, as_index=False).agg({
            impressions_col: "sum",
            clicks_col: "sum",
            orders_col: "sum",
            gmv_col: "sum"
        })

        # Merge with cost
        merged = pd.merge(
            cost_df[[product_id_col, product_name_col, cost_col]],
            creative_grouped,
            left_on=product_id_col,
            right_on=creative_id_col,
            how="left"
        )

        # Fill missing values
        merged.fillna(0, inplace=True)

        # Rename columns
        merged.rename(columns={
            product_id_col: "Product ID",
            product_name_col: "Product Name",
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

        # Round
        merged = merged.round(2)

        # Final column order
        final_columns = ["Product ID", "Product Name", "Cost", "Impressions", "Clicks", "Orders", "Gross Revenue", "CPM", "CPC", "CTR", "CR", "ROAS", "CPP"]
        merged = merged[[c for c in final_columns if c in merged.columns]]

        st.success("✅ Final ROAS Table:")
        st.dataframe(merged)

        # Download
        csv = merged.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Final ROAS Report", data=csv, file_name="ROAS_Report.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Error: {e}")
