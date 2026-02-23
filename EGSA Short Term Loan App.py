# EGSA Short Term Loan App - CSV/Excel Compatible
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="EGSA Short Term Loan App", layout="wide")
st.title("EGSA Short Term Loan Management")

# 1️⃣ Upload file (Excel or CSV)
uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=["xlsx", "xls", "csv"])

if uploaded_file:
    # 2️⃣ Read file based on extension
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # 3️⃣ Ensure required columns exist
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
        valid_types = ['level_1','level_2','level_3','level_4']
        df = df[df['loan_type'].isin(valid_types)]
        
        # 5️⃣ Set default status
        df['status'] = df['status'].fillna('in progress')
        
        # 6️⃣ Convert due_date to datetime
        df['due_date'] = pd.to_datetime(df['due_date'])
        
        # 7️⃣ Auto-update status if due_date <= today
        today = pd.to_datetime(date.today())
        df.loc[(df['due_date'] <= today) & (df['status'] == 'in progress'), 'status'] = 'completed'
        
        # 8️⃣ Display summary
        st.subheader("Loans Summary")
        st.write(f"Total loans: {len(df)}")
        st.write(f"In Progress: {len(df[df['status']=='in progress'])}")
        st.write(f"Completed: {len(df[df['status']=='completed'])}")
        
        # 9️⃣ Show tables
        st.subheader("In Progress Loans")
        st.dataframe(df[df['status']=='in progress'])
        
        st.subheader("Completed Loans")
        st.dataframe(df[df['status']=='completed'])
        
        # 10️⃣ Optional: Download updated file
        def to_excel(df):
            from io import BytesIO
            output = BytesIO()
            # Use context manager to automatically save/close
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Loans')
            processed_data = output.getvalue()
            return processed_data

        st.download_button(
            label="Download Updated Excel",
            data=to_excel(df),
            file_name="EGSA_short_term_loans_updated.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )