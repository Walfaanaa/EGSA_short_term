# EGSA Short Term Loan App - FINAL VERSION (Correct Urgent Filter)

import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="EGSA Short Term Loan App", layout="wide")
st.title("EGSA Short Term Loan Management")

# 1️⃣ Upload file or load from GitHub
uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=["xlsx", "xls", "csv"])
github_url = "https://raw.githubusercontent.com/Walfaanaa/EGSA_short_term/main/EGSA2025_short_loan.csv"

if st.button("Load default CSV from GitHub"):
    uploaded_file = github_url

if uploaded_file:
    try:
        # 2️⃣ Read file
        if isinstance(uploaded_file, str):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        # 3️⃣ Required columns
        required_columns = [
            "loan_id", "business_date", "id", "loan_type", "disbursed_amount",
            "interest_rate", "interest_amount", "collection_amount",
            "from_account", "to_account", "due_date", "Phone_no", "status"
        ]

        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            st.error(f"Missing columns in your file: {missing_cols}")

        else:
            # 4️⃣ Validate loan_type
            valid_types = ['level_1', 'level_2', 'level_3', 'level_4']
            df = df[df['loan_type'].isin(valid_types)]

            # 5️⃣ Clean status
            df['status'] = df['status'].fillna('in progress').str.lower()

            # 6️⃣ Convert due_date
            df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')

            # 7️⃣ Calculate days left
            today = pd.to_datetime(date.today())
            df['days_left'] = (df['due_date'] - today).dt.days

            # 8️⃣ Update status automatically
            df.loc[df['days_left'] <= 0, 'status'] = 'completed'
            df.loc[df['days_left'] == 1, 'status'] = '1 day left'
            df.loc[df['days_left'] == 2, 'status'] = '2 days left'
            df.loc[df['days_left'] > 2, 'status'] = 'in progress'

            # 9️⃣ Summary Dashboard
            st.subheader("Loans Summary")

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Total Loans", len(df))
            col2.metric("In Progress", len(df[df['status'] == 'in progress']))
            col3.metric("2 Days Left", len(df[df['status'] == '2 days left']))
            col4.metric("1 Day Left", len(df[df['status'] == '1 day left']))
            col5.metric("Completed", len(df[df['status'] == 'completed']))

            # 🔟 Urgent Loans (ONLY 1 or 2 days left)
            st.subheader("⚠️ Loans Due Soon (1–2 Days Only)")

            urgent_loans = df[df['status'].isin(['1 day left', '2 days left'])]

            if urgent_loans.empty:
                st.info("No urgent loans 🎉")
            else:
                st.dataframe(urgent_loans)

            # 1️⃣1️⃣ In Progress Loans
            st.subheader("In Progress Loans")
            st.dataframe(df[df['status'] == 'in progress'])

            # 1️⃣2️⃣ Completed Loans
            st.subheader("Completed Loans")
            st.dataframe(df[df['status'] == 'completed'])



        # 1️⃣5️⃣ Financial Summary
st.subheader("💰 Financial Summary")

# Ensure numeric (important if data comes as text)
df['disbursed_amount'] = pd.to_numeric(df['disbursed_amount'], errors='coerce').fillna(0)
df['interest_amount'] = pd.to_numeric(df['interest_amount'], errors='coerce').fillna(0)
df['collection_amount'] = pd.to_numeric(df['collection_amount'], errors='coerce').fillna(0)

total_disbursed = df['disbursed_amount'].sum()
total_interest = df['interest_amount'].sum()
total_collection = df['collection_amount'].sum()

col1, col2, col3 = st.columns(3)

col1.metric("Total Disbursed", f"{total_disbursed:,.2f}")
col2.metric("Total Interest", f"{total_interest:,.2f}")
col3.metric("Total Collection", f"{total_collection:,.2f}")

            # 1️⃣3️⃣ All Loans
            st.subheader("All Loans with Days Left")
            st.dataframe(df)

            # 1️⃣4️⃣ Download updated Excel
            def to_excel(dataframe):
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    dataframe.to_excel(writer, index=False, sheet_name='Loans')
                return output.getvalue()

            st.download_button(
                label="Download Updated Excel",
                data=to_excel(df),
                file_name="EGSA_short_term_loans_updated.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Error reading file: {e}")
