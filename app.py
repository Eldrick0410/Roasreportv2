import streamlit as st
import pandas as pd

st.title("ROAS Metrics Generator with Monthly Summary")

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

        # Ensure required columns exist
        required_file1_cols = {"product id", "cost"}
        required_file2_cols = {"product id", "impressions", "clicks", "gmv", "items sold"}

        if not required_file1_cols.issubset(df1.columns):
            st.error(f"File 1 is missing required columns: {required_file1_cols - set(df1.columns)}")
        elif not required_file2_cols.issubset(df2.columns):
            st.error(f"File 2 is missing required columns: {required_file2_cols - set(df2.columns)}")
        else:
            # Aggregate file 2
            df2_grouped = df2.groupby("product id", as_index=False).agg({
                "impressions": "sum",
                "clicks": "sum",
                "gmv": "sum",
                "items sold": "sum"
            })

            # Merge with file 1
            merged = pd.merge(df1, df2_grouped, on="product id", how="left")
            merged.fillna(0, inplace=True)

            # Calculate metrics
            merged["cpm"] = merged.apply(lambda row: (row["cost"] / row["impressions"] * 1000) if row["impressions"] else 0, axis=1)
            merged["cpc"] = merged.apply(lambda row: (row["cost"] / row["clicks"]) if row["clicks"] else 0, axis=1)
            merged["ctr"] = merged.apply(lambda row: (row["clicks"] / row["impressions"]) if row["impressions"] else 0, axis=1)  # decimal
            merged["cr"] = merged.apply(lambda row: (row["items sold"] / row["clicks"]) if row["clicks"] else 0, axis=1)  # decimal
            merged["roas"] = merged.apply(lambda row: (row["gmv"] / row["cost"]) if row["cost"] else 0, axis=1)

            # Reorder columns for final output
            final_columns = [
                "product id", "cost", "impressions", "cpm", "clicks", "cpc", "ctr",
                "items sold", "cr", "gmv", "roas"
            ]
            final_df = merged[final_columns]

            # Format numeric columns to 2 decimals for display
            display_df = final_df.copy()
            for col in ["cost", "cpm", "cpc", "ctr", "cr", "gmv", "roas"]:
                display_df[col] = display_df[col].round(2)

            st.success("✅ Metrics calculated successfully!")
            st.dataframe(display_df)

            # ----- Monthly Summary Table -----
            total_spend = final_df["cost"].sum()
            total_orders = final_df["items sold"].sum()
            total_gmv = final_df["gmv"].sum()
            total_roas = total_gmv / total_spend if total_spend else 0

            summary_df = pd.DataFrame([{
                "Spend ($)": round(total_spend, 2),
                "Orders": int(total_orders),
                "GMV ($)": round(total_gmv, 2),
                "ROAS": round(total_roas, 2)
            }])

            st.subheader("📊 Monthly Performance Summary")
            st.dataframe(summary_df)

            # ----- Download Section (Only Raw Decimal Data) -----
            csv_raw = final_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download ROAS Raw Data (Decimal %)",
                data=csv_raw,
                file_name="roas_raw.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
