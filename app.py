import streamlit as st
import pandas as pd

st.title("ROAS Metrics Generator")

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

            # Fill NaN with 0
            merged.fillna(0, inplace=True)

            # Calculated metrics
            merged["cpm"] = merged.apply(lambda row: (row["cost"] / row["impressions"] * 1000) if row["impressions"] else 0, axis=1)
            merged["cpc"] = merged.apply(lambda row: (row["cost"] / row["clicks"]) if row["clicks"] else 0, axis=1)
            merged["ctr"] = merged.apply(lambda row: (row["clicks"] / row["impressions"] * 100) if row["impressions"] else 0, axis=1)
            merged["cr"] = merged.apply(lambda row: (row["items sold"] / row["clicks"] * 100) if row["clicks"] else 0, axis=1)
            merged["roas"] = merged.apply(lambda row: (row["gmv"] / row["cost"]) if row["cost"] else 0, axis=1)

            # Reorder columns
            final_columns = [
                "product id", "cost", "impressions", "cpm", "clicks", "cpc", "ctr",
                "items sold", "cr", "gmv", "roas"
            ]
            final_df = merged[final_columns]

            st.success("✅ Metrics calculated successfully!")
            st.dataframe(final_df)

            # --- Download Section ---

            # 1. Human-readable CSV (percentages)
            csv_final = final_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Metrics (Readable %)",
                data=csv_final,
                file_name="roas_report.csv",
                mime="text/csv"
            )

            # 2. Raw CSV (percentages as decimal)
            raw_df = final_df.copy()
            percentage_cols = ["ctr", "cr"]  # convert to decimals
            raw_df[percentage_cols] = raw_df[percentage_cols] / 100

            csv_raw = raw_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Raw Data (Decimal %)",
                data=csv_raw,
                file_name="roas_raw.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")


'''
import streamlit as st
import pandas as pd

st.title("ROAS Metrics Generator")

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

            # Fill NaN with 0
            merged.fillna(0, inplace=True)

            # Calculated metrics
            merged["cpm"] = merged.apply(lambda row: (row["cost"] / row["impressions"] * 1000) if row["impressions"] else 0, axis=1)
            merged["cpc"] = merged.apply(lambda row: (row["cost"] / row["clicks"]) if row["clicks"] else 0, axis=1)
            merged["ctr"] = merged.apply(lambda row: (row["clicks"] / row["impressions"] * 100) if row["impressions"] else 0, axis=1)
            merged["cr"] = merged.apply(lambda row: (row["items sold"] / row["clicks"] * 100) if row["clicks"] else 0, axis=1)
            merged["roas"] = merged.apply(lambda row: (row["gmv"] / row["cost"]) if row["cost"] else 0, axis=1)

            # Reorder columns
            final_columns = [
                "product id", "cost", "impressions", "cpm", "clicks", "cpc", "ctr",
                "items sold", "cr", "gmv", "roas"
            ]
            final_df = merged[final_columns]

            st.success("✅ Metrics calculated successfully!")
            st.dataframe(final_df.style.format({
    "cost": "{:,.2f}", "cpm": "{:,.2f}", "cpc": "{:,.2f}",
    "ctr": "{:.2f}%", "cr": "{:.2f}%", "gmv": "{:,.2f}", "roas": "{:.2f}"
}), use_container_width=True)


            # Download button
            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Results as CSV", data=csv, file_name="roas_report.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
'''
