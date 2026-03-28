# EGSA Short Term Loan App - PRODUCTION VERSION

import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO

# -------------------- CONFIG --------------------
st.set_page_config(page_title="EGSA Short Term Loan App", layout="wide")
st.title("📊 EGSA Short Term Loan Management")

# -------------------- SESSION STATE --------------------
if "data_source" not in st.session_state:
    st.session_state.data_source = None

# -------------------- FILE INPUT --------------------
uploaded_file = st.file_uploader(
    "Upload your Excel or CSV file",
    type=["xlsx", "xls", "csv"]
)

github_url = "https://raw.githubusercontent.com/Walfaanaa/EGSA_short_term/main/EGSA2025_short_loan.xlsx"

if st.button("Load Default File from GitHub"):
    st.session_state.data_source = github_url

if uploaded_file is not None:
    st.session_state.data_source = uploaded_file

# -------------------- READ DATA --------------------
def load_data(source):
    try:
        if isinstance(source, str):
            # GitHub URL
            if source.endswith(".xlsx"):
                return pd.read_excel(source)
            else:
                try:
                    return pd.read_csv(source, encoding='utf-8')
                except:
                    return pd.read_csv(source, encoding='latin-1')

        else:
            # Uploaded file
            if source.name.endswith((".xlsx", ".xls")):
                return pd.read_excel(source)
            else:
                try:
                    return pd.read_csv(source, encoding='utf-8')
                except:
                    return pd.read_csv(source, encoding='latin-1')

    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

# -------------------- PROCESS --------------------
if st.session_state.data_source:

    df = load_data(st.session_state.data_source)

    if df is not None:

        # Required columns
        required_columns = [
            "loan_id", "business_date", "id", "loan_type", "disbursed_amount",
            "interest_rate", "interest_amount", "collection_amount",
            "from_account", "to_account", "due_date", "Phone_no", "status"
        ]

        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            st.error(f"❌ Missing columns: {missing_cols}")
            st.stop()

        # -------------------- CLEANING --------------------
        valid_types = ['level_1', 'level_2', 'level_3', 'level_4']
        df = df[df['loan_type'].isin(valid_types)]

        df['status'] = df['status'].fillna('in progress').str.lower()
        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')

        # Convert numeric safely
        for col in ['disbursed_amount', 'interest_amount', 'collection_amount']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # -------------------- DAYS CALCULATION --------------------
        today = pd.Timestamp.today().normalize()
        df['days_left'] = (df['due_date'] - today).dt.days

        # -------------------- STATUS LOGIC --------------------
        df.loc[(df['days_left'] <= 0) & (df['collection_amount'] >= df['disbursed_amount']), 'status'] = 'completed'
        df.loc[(df['days_left'] <= 0) & (df['collection_amount'] < df['disbursed_amount']), 'status'] = 'overdue'
        df.loc[df['days_left'] == 1, 'status'] = '1 day left'
        df.loc[df['days_left'] == 2, 'status'] = '2 days left'
        df.loc[df['days_left'] > 2, 'status'] = 'in progress'

        # -------------------- SIDEBAR FILTER --------------------
        st.sidebar.header("🔍 Filter Loans")

        status_filter = st.sidebar.multiselect(
            "Select Status",
            options=df['status'].unique(),
            default=df['status'].unique()
        )

        search_id = st.sidebar.text_input("Search by ID")

        filtered_df = df[df['status'].isin(status_filter)]

        if search_id:
            filtered_df = filtered_df[
                filtered_df['id'].astype(str).str.contains(search_id)
            ]

        # -------------------- SUMMARY --------------------
        st.subheader("📌 Loan Summary")

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("Total", len(df))
        col2.metric("In Progress", len(df[df['status'] == 'in progress']))
        col3.metric("2 Days Left", len(df[df['status'] == '2 days left']))
        col4.metric("1 Day Left", len(df[df['status'] == '1 day left']))
        col5.metric("Completed", len(df[df['status'] == 'completed']))
        col6.metric("Overdue", len(df[df['status'] == 'overdue']))

        # -------------------- URGENT --------------------
        st.subheader("⚠️ Urgent Loans (1–2 Days)")
        urgent = df[df['status'].isin(['1 day left', '2 days left'])]

        if urgent.empty:
            st.success("No urgent loans ✅")
        else:
            st.dataframe(urgent)

        # -------------------- OVERDUE --------------------
        st.subheader("🚨 Overdue Loans")
        overdue = df[df['status'] == 'overdue']

        if overdue.empty:
            st.success("No overdue loans ✅")
        else:
            st.dataframe(overdue)

        # -------------------- TABLE --------------------
        st.subheader("📋 Filtered Loans")
        st.dataframe(filtered_df)

        # -------------------- FINANCIAL SUMMARY --------------------
        st.subheader("💰 Financial Summary")

        total_disbursed = df['disbursed_amount'].sum()
        total_interest = df['interest_amount'].sum()
        total_collection = df['collection_amount'].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Disbursed", f"{total_disbursed:,.2f}")
        col2.metric("Total Interest", f"{total_interest:,.2f}")
        col3.metric("Total Collection", f"{total_collection:,.2f}")

        # -------------------- DOWNLOAD --------------------
        def to_excel(dataframe):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                dataframe.to_excel(writer, index=False, sheet_name='Loans')
            return output.getvalue()

        st.download_button(
            label="⬇️ Download Updated Excel",
            data=to_excel(df),
            file_name="EGSA_short_term_loans_updated.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
