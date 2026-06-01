import streamlit as st
from utils import filter_deals

st.set_page_config(page_title="Lease Score Demo", page_icon="🚗", layout="wide")

import streamlit as st
import pandas as pd

# 1. Add the file uploader widget
uploaded_file = st.file_uploader("Choose a file", type=["csv"])

# 2. Check if a file has been uploaded
if uploaded_file is not None:

    # 3. Read and display the file based on its type
    if uploaded_file.name.endswith('.csv'):
        # Read CSV
        all_deals = pd.read_csv(uploaded_file)

    else:
        st.error("Only .csv files are accepted.")
        st.stop()

    expected_columns = [
        "quote_id",
        "make",
        "model",
        'derivative',
        "fuel_type",
        "price_new_inc_vat",
        "monthly_payment",
        "term_months",
        "deposit_months",
        "deposit_amount",
        "annual_mileage",
        'PCP_monthly',
        'leasing_monthly_over_PCP',
        'residual_value'
    ]

    missing_cols = set(expected_columns) - set(all_deals.columns)

    if missing_cols:
        st.error(f"Required columns missing in file: {missing_cols}")
        st.stop()

    all_deals = all_deals[all_deals['PCP_monthly']>0]
    all_deals['monthly_payment_over_price_new_inc_vat'] = all_deals['monthly_payment']/all_deals['price_new_inc_vat']
    all_deals['depreciation'] = all_deals['price_new_inc_vat'] - all_deals['residual_value']
    all_deals['total_payment'] = (all_deals['term_months']+all_deals['deposit_months'])*all_deals['monthly_payment']
    all_deals['total_payment_over_list_price'] = all_deals['total_payment']/all_deals['price_new_inc_vat']
    all_deals['total_payment_over_depreciation'] = all_deals['total_payment']/all_deals['depreciation']
    terms_options = sorted(all_deals["term_months"].dropna().unique().tolist())
    make_options = sorted(all_deals["make"].dropna().unique().tolist())
    fuel_type_options = sorted(all_deals["fuel_type"].dropna().unique().tolist())


    boundaries = {
        'deposit_amount':(all_deals['deposit_amount'].min(),all_deals['deposit_amount'].max()),
        'monthly_payment':(all_deals['monthly_payment'].min(), all_deals['monthly_payment'].max()),
    }

    make_model_dict = all_deals.groupby('make')['model'].unique().to_dict()
    make_model_derivative_dict = all_deals.groupby(['make', 'model'])['derivative'].unique().to_dict()
    st.title("Lease Score Demo")

    st.write("Enter the lease details below.")

    left_col, right_col = st.columns([2, 2])

    with left_col:

        monthly_payment = st.selectbox(
            "Maximum monthly price (£)",
            [150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000, 2000, 3000],
            index=7
        )

        initial_payment = st.selectbox(
            "Maximum Initial payment (£)",
            [1000, 2000, 3000, 4000, 5000, 10000, 20000, 30000],
            index=1,
        )

        term_months = st.multiselect(
            label="Term (months)",
            options=terms_options,
            default=[24] ,
        )

        annual_mileage = st.selectbox(
            "Maximum miles per year",
            [5000, 8000, 10000, 12000, 15000, 20000],
            index=1
        )

        fuel_type = st.selectbox(
            "Fuel Type",
            options=["Any"] + fuel_type_options,
        )

        make = st.selectbox(
            "Make",
            options=["Any"] + make_options,
        )

        if make!='Any':
            model_options = sorted(list(make_model_dict[make]))
            model = st.selectbox(
                "Model",
                options=['Any']+model_options,
            )
        else:
            model='Any'

        if model!='Any':
            derivative_options = sorted(list(make_model_derivative_dict[(make, model)]))
            derivative = st.selectbox(
                "Derivative",
                options=['Any'] + derivative_options,
            )
        else:
            derivative = 'Any'

    with right_col:
        st.subheader("Selected filters:")
        st.write(f"**Maximum Monthly payment:** £{monthly_payment:,.2f}")
        st.write(f"**Maximum Initial payment:** £{initial_payment:,.2f}")
        st.write(f"**Maximum Miles per Year:** {annual_mileage}")
        st.write(f"**Term:** {term_months} months")
        if fuel_type!='Any':
            st.write(f"**Fuel Type:** {fuel_type}")
        if make!='Any':
            st.write(f"**Make:** {make}")
        if model!='Any':
            st.write(f"**Model:** {model}")
        if derivative!='Any':
            st.write(f"**Derivative:** {derivative}")

    display_columns = [
        "quote_id",
        "make",
        "model",
        'derivative',
        "fuel_type",
        "price_new_inc_vat",
        "monthly_payment",
        "term_months",
        "deposit_months",
        "deposit_amount",
        "annual_mileage",
        'total_payment',
        'residual_value',
        'depreciation',
        'PCP_monthly',
        'leasing_monthly_over_PCP',
    ]

    # gather the filters
    filters = {
        'max_monthly_payment': monthly_payment,
        'max_initial_payment': initial_payment,
        'max_annual_mileage': annual_mileage,
        'term_months': term_months,
    }
    if make!='Any':
        filters['make'] = make
    if model!='Any':
        filters['model'] = model
    if derivative!='Any':
        filters['derivative'] = derivative
    if fuel_type!='Any':
        filters['fuel_type'] = fuel_type

    selected_deals = filter_deals(all_deals, filters)

    if selected_deals.empty:
        st.error("No deals available with selected filters.")
    else:
        st.subheader("Top deals")
        sort_order = st.radio(
            "Sort by:",
            [
                'Monthly payment (Low->High)',
                "Monthly payment over list price (Low->High)",
                "Total payment over list price (Low->High)",
                "Total payment over depreciation (Low->High)",
                "**Monthly payment over PCP** (Low->High)"
            ]
        )
        if sort_order == "Monthly payment (Low->High)":
            data_for_display = selected_deals.sort_values("monthly_payment")[display_columns]
        elif sort_order == "Monthly payment over list price (Low->High)":
            data_for_display = selected_deals.sort_values("monthly_payment_over_price_new_inc_vat")[display_columns]
        elif sort_order == "Total payment over list price (Low->High)":
            data_for_display = selected_deals.sort_values("total_payment_over_list_price")[display_columns]
        elif sort_order == "Total payment over depreciation (Low->High)":
            data_for_display = selected_deals.sort_values("total_payment_over_depreciation")[display_columns]
        else:
            data_for_display = selected_deals.sort_values('leasing_monthly_over_PCP')[display_columns]

        st.dataframe(
            data_for_display.head(100),
            hide_index=True,
            width='stretch',
        )