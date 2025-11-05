import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Staff Cross-Check", layout="wide")
st.title("🧾 Aloha vs Application — Differences Only (with counts)")

st.write(
    "1️⃣ **Aloha Billing Manager File** → column: `Staff`\n"
    "2️⃣ **Clean file from application** → column: `Staff Name`\n\n"
    "This will show ONLY names where counts don't match or the name is missing in one file."
)

aloha_file = st.file_uploader("1️⃣ Upload Aloha Billing Manager File", type=["csv", "xlsx", "xls"])
clean_file = st.file_uploader("2️⃣ Upload Clean file from application", type=["csv", "xlsx", "xls"])

def read_any(file):
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

if aloha_file and clean_file:
    df_aloha = read_any(aloha_file)
    df_clean = read_any(clean_file)

    if "Staff" not in df_aloha.columns:
        st.error("1st file must have a column named 'Staff'.")
    elif "Staff Name" not in df_clean.columns:
        st.error("2nd file must have a column named 'Staff Name'.")
    else:
        # normalize to one column
        aloha = df_aloha[["Staff"]].rename(columns={"Staff": "Name"}).dropna()
        clean = df_clean[["Staff Name"]].rename(columns={"Staff Name": "Name"}).dropna()

        # strip spaces
        aloha["Name"] = aloha["Name"].astype(str).str.strip()
        clean["Name"] = clean["Name"].astype(str).str.strip()

        # count occurrences in each file
        aloha_counts = (
            aloha.value_counts("Name")
            .rename("Count_Aloha")
            .reset_index()
        )
        clean_counts = (
            clean.value_counts("Name")
            .rename("Count_Clean")
            .reset_index()
        )

        # outer merge to compare
        merged = pd.merge(
            aloha_counts,
            clean_counts,
            on="Name",
            how="outer"
        ).fillna(0)

        # make them ints
        merged["Count_Aloha"] = merged["Count_Aloha"].astype(int)
        merged["Count_Clean"] = merged["Count_Clean"].astype(int)

        # figure out where it's missing
        def missing_from(row):
            a = row["Count_Aloha"]
            c = row["Count_Clean"]
            if a > 0 and c > 0:
                if a != c:
                    return "Counts differ"
                return ""   # same → we'll drop
            if a > 0 and c == 0:
                return "Clean file"
            if a == 0 and c > 0:
                return "Aloha file"
            return "Both"

        merged["Missing From"] = merged.apply(missing_from, axis=1)

        # keep only the problem rows
        diffs = merged[merged["Missing From"] != ""].sort_values("Name").reset_index(drop=True)

        st.subheader("⚠️ Differences (names missing or counts different)")
        if diffs.empty:
            st.success("No differences found — names and counts match.")
        else:
            st.dataframe(diffs, use_container_width=True)

            # export to excel (openpyxl)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                diffs.to_excel(writer, index=False, sheet_name="Differences")
            buffer.seek(0)

            st.download_button(
                label="⬇️ Download differences (Excel)",
                data=buffer,
                file_name="staff_differences_with_counts.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("Upload both files to run the check.")
