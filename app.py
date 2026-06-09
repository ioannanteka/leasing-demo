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
        all_deals = pd.read_csv(uploaded_file)import streamlit as st
import pandas as pd
from utils import filter_deals

st.set_page_config(page_title="Lease Score Demo", page_icon="🚗", layout="wide")

# Initialize session state for data storage if it doesn't exist
if "all_deals" not in st.session_state:
    st.session_state.all_deals = None

# 1. Add the file uploader widget
uploaded_file = st.file_uploader("Choose a file", type=["csv"])

# 2. Check if a file has been uploaded and process it
if uploaded_file is not None:
    if uploaded_file.name.endswith('.csv'):
        # Only read the file once and store it in session state to prevent crashing on widget changes
        if st.session_state.all_deals is None:
            df = pd.read_csv(uploaded_file)

            expected_columns = [
                "quote_id", "make", "model", 'derivative', "fuel_type",
                "price_new_inc_vat", "monthly_payment", "term_months",
                "deposit_months", "deposit_amount", "annual_mileage",
                'PCP_monthly', 'leasing_monthly_over_PCP', 'residual_value'
            ]

            missing_cols = set(expected_columns) - set(df.columns)
            if missing_cols:
                st.error(f"Required columns missing in file: {missing_cols}")
                st.stop()

            # Perform calculations once and store the result
            df = df[df['PCP_monthly'] > 0].copy()
            df['monthly_payment_over_price_new_inc_vat'] = df['monthly_payment'] / df['price_new_inc_vat']
            df['depreciation'] = df['price_new_inc_vat'] - df['residual_value']
            df['total_payment'] = (df['term_months'] + df['deposit_months']) * df['monthly_payment']
            df['total_payment_over_list_price'] = df['total_payment'] / df['price_new_inc_vat']
            df['total_payment_over_depreciation'] = df['total_payment'] / df['depreciation']

            st.session_state.all_deals = df
    else:
        st.error("Only .csv files are accepted.")
        st.stop()
else:
    # Reset state if the user removes the file
    st.session_state.all_deals = None
    st.info("Please upload a CSV file to begin.")
    st.stop()

# Retrieve the persistent data from session state
all_deals = st.session_state.all_deals

# Generate option lists safely from cached dataframe
terms_options = sorted(all_deals["term_months"].dropna().unique().tolist())
make_options = sorted(all_deals["make"].dropna().unique().tolist())
fuel_type_options = sorted(all_deals["fuel_type"].dropna().unique().tolist())

make_model_dict = all_deals.groupby('make')['model'].unique().to_dict()
make_model_derivative_dict = all_deals.groupby(['make', 'model'])['derivative'].unique().to_dict()

st.title("Lease Score Demo")
st.write("Enter the lease details below.")

left_col, right_col = st.columns(2)

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
        default=[24] if 24 in terms_options else [terms_options[0]] if terms_options else [],
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

    # Dynamic dependent dropdown structures
    if make != 'Any' and make in make_model_dict:
        model_options = sorted(list(make_model_dict[make]))
        model = st.selectbox(
            "Model",
            options=['Any'] + model_options,
        )
    else:
        model = 'Any'

    if model != 'Any' and (make, model) in make_model_derivative_dict:
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
    if fuel_type != 'Any':
        st.write(f"**Fuel Type:** {fuel_type}")
    if make != 'Any':
        st.write(f"**Make:** {make}")
    if model != 'Any':
        st.write(f"**Model:** {model}")
    if derivative != 'Any':
        st.write(f"**Derivative:** {derivative}")

display_columns = [
    "quote_id", "make", "model", 'derivative', "fuel_type",
    "price_new_inc_vat", "monthly_payment", "term_months",
    "deposit_months", "deposit_amount", "annual_mileage",
    'total_payment', 'residual_value', 'depreciation',
    'PCP_monthly', 'leasing_monthly_over_PCP',
]

# Gather the filters
filters = {
    'max_monthly_payment': monthly_payment,
    'max_initial_payment': initial_payment,
    'max_annual_mileage': annual_mileage,
    'term_months': term_months,
}
if make != 'Any': filters['make'] = make
if model != 'Any': filters['model'] = model
if derivative != 'Any': filters['derivative'] = derivative
if fuel_type != 'Any': filters['fuel_type'] = fuel_type

selected_deals = filter_deals(all_deals, filters)

if selected_deals.empty:
    st.error("No deals available with selected filters.")
else:
    order_specifications = {
        'Monthly payment (Low->High)': {'col': 'monthly_payment', 'ascending': True},
        "Monthly payment over list price (Low->High)": {'col': 'monthly_payment_over_price_new_inc_vat',
                                                        'ascending': True},
        "Total payment over list price (Low->High)": {'col': 'total_payment_over_list_price', 'ascending': True},
        "Total payment over depreciation (Low->High)": {'col': 'total_payment_over_depreciation', 'ascending': True},
        "**Monthly payment over PCP** (Low->High)": {'col': 'leasing_monthly_over_PCP', 'ascending': True},
    }

    st.subheader("Sort order comparison\n Select two sort orders to compare top results")
    N = st.number_input("Number of results to display:", min_value=10, max_value=100, step=10, value=10)

    ref_order_section, alternative_order_section = st.columns(2)

    with ref_order_section:
        ref_order = st.radio("Reference Order", list(order_specifications.keys()), index=1)
        order_spec = order_specifications[ref_order]
        data_sorted_ref = selected_deals.sort_values(order_spec['col'], ascending=order_spec['ascending'])

        st.dataframe(data_sorted_ref[display_columns].head(N), hide_index=True, use_container_width=True)

        st.write('Summary stats for reference order:')
        st.dataframe(
            data_sorted_ref[
                ['monthly_payment', 'deposit_amount', 'total_payment', 'PCP_monthly', 'leasing_monthly_over_PCP']].head(
                N).describe(),
            hide_index=False,
            use_container_width=True,
        )

    with alternative_order_section:
        alternative_order = st.radio("Alternative Order", list(order_specifications.keys()), index=4)
        order_spec = order_specifications[alternative_order]
        data_sorted_alternative = selected_deals.sort_values(order_spec['col'], ascending=order_spec['ascending'])

        st.dataframe(data_sorted_alternative[display_columns].head(N), hide_index=True, use_container_width=True)

        st.write('Summary stats for alternative order:')
        st.dataframe(
            data_sorted_alternative[
                ['monthly_payment', 'deposit_amount', 'total_payment', 'PCP_monthly', 'leasing_monthly_over_PCP']].head(
                N).describe(),
            hide_index=False,
            use_container_width=True,
        )

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

    left_col, right_col = st.columns(2)

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

        order_specifications = {
            'Monthly payment (Low->High)':{'col':'monthly_payment', 'ascending':True},
            "Monthly payment over list price (Low->High)":{'col':'monthly_payment_over_price_new_inc_vat', 'ascending':True},
            "Total payment over list price (Low->High)":{'col':'total_payment_over_list_price', 'ascending':True},
            "Total payment over depreciation (Low->High)":{'col':'total_payment_over_depreciation', 'ascending':True},
            "**Monthly payment over PCP** (Low->High)":{'col':'leasing_monthly_over_PCP', 'ascending':True},
        }

        st.subheader("Sort order comparison\n Select two sort orders to compare top results")
        N = st.number_input("Number of results to display:", min_value=10, max_value=100, step=10, value=10)
        ref_order_section, alternative_order_section = st.columns(2)
        with ref_order_section:
            ref_order = st.radio(
                "Reference Order",
                list(order_specifications.keys()),
                index=1,
            )

            order_spec = order_specifications[ref_order]
            data_sorted_ref = selected_deals.sort_values(order_spec['col'], ascending=order_spec['ascending'])

            st.dataframe(
                data_sorted_ref[display_columns].head(N),
                hide_index=True,
                width='stretch',
            )

            # calculate stats
            st.write('Summary stats for reference order:')
            # calculate stats
            st.dataframe(
                data_sorted_ref[['monthly_payment', 'deposit_amount', 'total_payment', 'PCP_monthly','leasing_monthly_over_PCP',]].head(N).describe(),
                hide_index=False,
                width='stretch',
            )

        with alternative_order_section:
            alternative_order = st.radio(
                "Alternative Order",
                list(order_specifications.keys()),
                index=4
            )

            order_spec = order_specifications[alternative_order]
            data_sorted_alternative = selected_deals.sort_values(order_spec['col'], ascending=order_spec['ascending'])

            st.dataframe(
                data_sorted_alternative[display_columns].head(N),
                hide_index=True,
                width='stretch',
            )

            # calculate stats
            st.write('Summary stats for alternative order:')
            st.dataframe(
                data_sorted_alternative[['monthly_payment', 'deposit_amount', 'total_payment', 'PCP_monthly', 'leasing_monthly_over_PCP',]].head(N).describe(),
                hide_index=False,
                width='stretch',
            )
