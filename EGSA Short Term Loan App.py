# ==================== EGSA SHORT TERM LOAN APP ====================

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

# -------------------- INPUT --------------------
uploaded_file = st.file_uploader(
    "Upload Excel or CSV file",
    type=["xlsx", "xls", "csv"]
)

github_url = "https://raw.githubusercontent.com/Walfaanaa/EGSA_short_term/main/EGSA2025_short_loan.xlsx"

if st.button("Load Default File from GitHub"):
    st.session_state.data_source = github_url

if uploaded_file is not None:
    st.session_state.data_source = uploaded_file


# -------------------- LOAD DATA --------------------
def load_data(source):
    try:
        if isinstance(source, str):
            if source.endswith(".xlsx"):
                return pd.read_excel(source)
            else:
                try:
                    return pd.read_csv(source, encoding="utf-8")
                except:
                    return pd.read_csv(source, encoding="latin-1")
        else:
            if source.name.endswith((".xlsx", ".xls")):
                return pd.read_excel(source)
            else:
                try:
                    return pd.read_csv(source, encoding="utf-8")
                except:
                    return pd.read_csv(source, encoding="latin-1")
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None


# -------------------- PROCESS --------------------
if st.session_state.data_source:

    df = load_data(st.session_state.data_source)

    if df is not None:

        # -------------------- REQUIRED COLUMNS --------------------
        required_columns = [
            "loan_id", "business_date", "id", "loan_type", "disbursed_amount",
            "interest_rate", "interest_amount", "collection_amount",
            "from_account", "to_account", "due_date", "Phone_no", "status"
        ]

        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            st.error(f"Missing columns: {missing}")
            st.stop()

        # -------------------- CLEANING --------------------
        valid_types = ['level_1', 'level_2', 'level_3', 'level_4', 'level_5', 'level_6']
        df = df[df['loan_type'].isin(valid_types)]

        df['status'] = df['status'].fillna('in progress').str.lower()
        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')

        for col in ['disbursed_amount', 'interest_amount', 'collection_amount']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # -------------------- DAYS CALCULATION --------------------
        today = pd.Timestamp.today().normalize()
        df['days_left'] = (df['due_date'] - today).dt.days

        # -------------------- STATUS LOGIC --------------------
        df.loc[
            (df['days_left'] <= 0) &
            (df['collection_amount'] >= df['disbursed_amount']),
            'status'
        ] = 'completed'

        df.loc[
            (df['days_left'] <= 0) &
            (df['collection_amount'] < df['disbursed_amount']),
            'status'
        ] = 'overdue'

        df.loc[df['days_left'] == 1, 'status'] = '1 day left'
        df.loc[df['days_left'] == 2, 'status'] = '2 days left'
        df.loc[df['days_left'] > 2, 'status'] = 'in progress'

        # -------------------- FILTER --------------------
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

        # -------------------- GROUPS --------------------
        in_progress_df = df[df['status'] == 'in progress']
        two_days_df = df[df['status'] == '2 days left']
        one_day_df = df[df['status'] == '1 day left']
        completed_df = df[df['status'] == 'completed']
        overdue_df = df[df['status'] == 'overdue']

        # -------------------- TOTALS --------------------
        def totals(data):
            return data['disbursed_amount'].sum(), data['collection_amount'].sum()

        in_d, in_c = totals(in_progress_df)
        comp_d, comp_c = totals(completed_df)
        ov_d, ov_c = totals(overdue_df)

        # -------------------- SUMMARY --------------------
        st.subheader("📌 Loan Summary")

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        col1.metric("Total Loans", len(df))

        col2.metric(
            "In Progress",
            len(in_progress_df),
            f"D:{in_d:,.0f} | C:{in_c:,.0f}"
        )

        col3.metric("2 Days Left", len(two_days_df))

        col4.metric("1 Day Left", len(one_day_df))

        col5.metric(
            "Completed",
            len(completed_df),
            f"D:{comp_d:,.0f} | C:{comp_c:,.0f}"
        )

        col6.metric(
            "Overdue",
            len(overdue_df),
            f"D:{ov_d:,.0f} | C:{ov_c:,.0f}"
        )

        # -------------------- URGENT --------------------
        st.subheader("⚠️ Urgent Loans (1–2 Days)")
        urgent = df[df['status'].isin(['1 day left', '2 days left'])]

        if urgent.empty:
            st.success("No urgent loans ✅")
        else:
            st.dataframe(urgent)

        # -------------------- OVERDUE --------------------
        st.subheader("🚨 Overdue Loans")

        if overdue_df.empty:
            st.success("No overdue loans ✅")
        else:
            st.dataframe(overdue_df)

        # -------------------- TABLE --------------------
        st.subheader("📋 Filtered Loans")
        st.dataframe(filtered_df)

        # -------------------- FINANCIAL SUMMARY --------------------
        st.subheader("💰 Financial Summary")

        total_disbursed = df['disbursed_amount'].sum()
        total_interest = df['interest_amount'].sum()
        total_collection = df['collection_amount'].sum()

        c1, c2, c3 = st.columns(3)

        c1.metric("Total Disbursed", f"{total_disbursed:,.0f}")
        c2.metric("Total Interest", f"{total_interest:,.0f}")
        c3.metric("Total Collection", f"{total_collection:,.0f}")

        # -------------------- KPIs --------------------
        st.subheader("📊 Advanced KPIs")

        recovery_rate = (
            comp_c / comp_d * 100
            if comp_d > 0 else 0
        )

        outstanding = in_d - in_c

        k1, k2, k3 = st.columns(3)

        k1.metric("Recovery Rate", f"{recovery_rate:.2f}%")
        k2.metric("Outstanding Balance", f"{outstanding:,.0f}")
        k3.metric(
            "Active Loans",
            len(in_progress_df) + len(two_days_df) + len(one_day_df)
        )

        # -------------------- CHARTS --------------------
        st.subheader("📈 Status Distribution")
        st.bar_chart(df['status'].value_counts())

        st.subheader("🥧 Portfolio Distribution")
        st.bar_chart(df.groupby("status")["disbursed_amount"].sum())

        # -------------------- DOWNLOAD --------------------
        def to_excel(dataframe):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                dataframe.to_excel(writer, index=False, sheet_name='Loans')
            return output.getvalue()

        st.download_button(
            "⬇️ Download Updated Excel",
            to_excel(df),
            file_name="EGSA_short_term_loans_updated.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
