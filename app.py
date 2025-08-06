import streamlit as st
import pandas as pd

st.title("ROAS Table Generator 🚀")

# --- File Upload ---
file1 = st.file_uploader("Upload File 1 (Product Cost)", type=["xlsx"])
file2 = st.file_uploader("Upload File 2 (Creative Metrics)", type=["xlsx"])
file3 = st.file_uploader("Optional: Product Name File", type=["xlsx"])

if file1 and file2:
    # --- Read Files ---
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    # Normalize column names
    df1.columns = df1.columns.str.strip().str.lower()
    df2.columns = df2.columns.str.strip().str.lower()

    # Detect Product ID column in both files
    pid_col1 = [c for c in df1.columns if "product" in c and "id" in c][0]
    pid_col2 = [c for c in df2.columns if "product" in c and "id" in c][0]

    # Convert to string for safe merging
    df1[pid_col1] = df1[pid_col1].astype(str)
    df2[pid_col2] = df2[pid_col2].astype(str)

    # --- Aggregate File 2 metrics ---
    agg_df2 = df2.groupby(pid_col2).agg({
        'impressions': 'sum',
        'clicks': 'sum',
        'gmv': 'sum'
    }).reset_index()

    # --- Merge files ---
    merged = pd.merge(df1, agg_df2, left_on=pid_col1, right_on=pid_col2, how='left')

    # --- Calculate Metrics ---
    merged['cpm'] = merged['cost'] / merged['impressions'] * 1000
    merged['cpc'] = merged['cost'] / merged['clicks']
    merged['ctr'] = merged['clicks'] / merged['impressions']
    merged['cr'] = merged['gmv'] / merged['clicks']
    merged['roas'] = merged['gmv'] / merged['cost']

    # Clean columns
    merged = merged.rename(columns={pid_col1: "Product ID"})[
        ["Product ID", "cost", "impressions", "cpm", "clicks", "cpc", "ctr", "gmv", "roas"]
    ]

    # --- Optional Product Name Merge ---
    if file3:
        df3 = pd.read_excel(file3)
        df3.columns = df3.columns.str.strip().str.lower()

        st.write("🔍 Debug: Product Name File Preview")
        st.dataframe(df3.head())  # Debug preview

        # Auto-detect columns
        pid_col3 = [c for c in df3.columns if "product" in c and "id" in c]
        pname_col = [c for c in df3.columns if "name" in c or "title" in c]

        if pid_col3 and pname_col:
            pid_col3 = pid_col3[0]
            pname_col = pname_col[0]

            df3[pid_col3] = df3[pid_col3].astype(str)
            merged["Product ID"] = merged["Product ID"].astype(str)

            merged = pd.merge(
                df3[[pid_col3, pname_col]],
                merged,
                left_on=pid_col3,
                right_on="Product ID",
                how="right"
            ).drop(columns=[pid_col3]).rename(columns={pname_col: "Product Name"})

        else:
            st.warning("⚠️ Could not auto-detect Product Name column. Skipping name merge.")

    # --- Final Output ---
    st.subheader("Final ROAS Table")
    st.dataframe(merged)

    # --- Download Button ---
    st.download_button(
        label="📥 Download ROAS Table",
        data=merged.to_csv(index=False).encode('utf-8'),
        file_name="roas_table.csv",
        mime="text/csv"
    )

else:
    st.info("⬆️ Please upload File 1 and File 2 to begin.")
