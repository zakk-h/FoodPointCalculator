import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Define the dining plans
dining_plans = {
    "Plan I (First-year students)": 946,
    "Plan A": 2747,
    "Plan B": 3292,
    "Plan C": 3645,
    "Plan D": 3912,
    "Plan E": 4267,
    "Plan F": 900,
    "Plan J": 1943,
    "Summer S": 798,
    "Summer M": 1119,
    "Summer L": 1478,
    "Custom": None
}

# Hardcoded term dates for 2024-2025, separating Summer Session 1 and 2
terms = [
    {"name": "Summer 2024 - Session 1", "start": "2024-05-15", "end": "2024-06-27"},
    {"name": "Summer 2024 - Session 2", "start": "2024-07-01", "end": "2024-08-11"},
    {"name": "Fall 2024", "start": "2024-08-26", "end": "2024-12-16"},
    {"name": "Spring 2025", "start": "2025-01-08", "end": "2025-05-03"},
    {"name": "Summer 2025 - Session 1", "start": "2025-05-14", "end": "2025-06-26"},
    {"name": "Summer 2025 - Session 2", "start": "2025-06-30", "end": "2025-08-11"}
]

# Function to determine the current or next term based on hardcoded dates
def get_term_dates():
    current_date = datetime.now()
    
    # Convert term start and end dates to datetime objects
    for term in terms:
        term['start'] = datetime.strptime(term['start'], "%Y-%m-%d")
        term['end'] = datetime.strptime(term['end'], "%Y-%m-%d")

    # Find the current term
    for term in terms:
        if term['start'] <= current_date <= term['end']:
            days_elapsed = (current_date - term['start']).days
            return term['start'], term['end'], days_elapsed, term['name']

    # If not within any term, find the next upcoming term
    future_terms = [term for term in terms if term['start'] > current_date]
    if future_terms:
        next_term = min(future_terms, key=lambda term: term['start'])
        return next_term['start'], next_term['end'], 0, next_term['name']

    # If no current or future term is found, return placeholders
    return None, None, 0, "No Active Term"

# Function to log data
def log_data(term_start_date, term_end_date, start_date, end_date, starting_points, current_points):
    log_entry = {
        "term_start_date": term_start_date,
        "term_end_date": term_end_date,
        "current_date": datetime.now(),
        "start_date": start_date,
        "end_date": end_date,
        "starting_points": starting_points,
        "current_points": current_points
    }
    try:
        # Load existing data
        df = pd.read_csv("food_points_log.csv")
        df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
    except FileNotFoundError:
        # If file doesn't exist, create a new DataFrame
        df = pd.DataFrame([log_entry])
    
    # Save the updated DataFrame
    df.to_csv("food_points_log.csv", index=False)

# Get term dates
term_start_date, term_end_date, days_elapsed, term_name = get_term_dates()

# Streamlit UI
st.title("Food Point Calculator")
st.markdown(f"### {term_name}")

if term_start_date is None or term_end_date is None:
    st.error("Could not determine the current term dates.")
else:
    # Input fields for start date, end date, and selecting a dining plan
    start_date = st.date_input("Start Date", term_start_date)
    end_date = st.date_input("End Date", term_end_date)

    if end_date < start_date:
        st.error("End date cannot be before start date.")
    else:
        plan_selected = st.selectbox("Select a Dining Plan", list(dining_plans.keys()))
        starting_points = st.number_input("Starting Food Points", value=dining_plans[plan_selected] if dining_plans[plan_selected] is not None else 0, min_value=0)
        
        if 'current_points' not in st.session_state:
            st.session_state.current_points = starting_points

        def log_current_points():
            current_points = st.session_state.current_points
            log_data(term_start_date, term_end_date, start_date, end_date, starting_points, current_points)
        
        st.number_input("Current Food Points", min_value=0, key='current_points', on_change=log_current_points)

        # Calculate the days elapsed and total days in the term
        days_elapsed = (datetime.now().date() - start_date).days
        total_days = (end_date - start_date).days
        days_remaining = (end_date - datetime.now().date()).days

        # Calculate points used and needed per day
        points_used = starting_points - st.session_state.current_points
        points_per_day_used = points_used / days_elapsed if days_elapsed > 0 else 0
        points_per_day_total = starting_points / total_days if total_days > 0 else 0
        points_per_day_from_now = st.session_state.current_points / days_remaining if days_remaining > 0 else 0
        over_under = st.session_state.current_points - days_remaining * points_per_day_used

        # Display the results
        st.write(f"Days elapsed: {days_elapsed}")
        st.write(f"Total days in term: {total_days}")
        if days_elapsed < 0: 
            st.write(f"You are able to spend {starting_points/total_days:.2f} food points per day once the term begins.")
            st.write(f"Additional statistics on food points and current trajectory will appear after the term begins on {start_date}.")
        else:
            st.write(f"Points used so far: {points_used}")
            st.write(f"Average points used per day: {points_per_day_used:.2f}")
            st.write(f"Allowed points to spend per day from now on: {points_per_day_from_now:.2f}")
            st.write(f"Food points remaining if current trajectory continues: {over_under:.2f}")
