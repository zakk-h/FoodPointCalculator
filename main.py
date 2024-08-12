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

# Hardcoded term dates and breaks for 2024-2025
terms = [
    {"name": "Summer 2024 - Session 1", "start": "2024-05-15", "end": "2024-06-27"},
    {"name": "Summer 2024 - Session 2", "start": "2024-07-01", "end": "2024-08-11"},
    {"name": "Fall 2024", "start": "2024-08-26", "end": "2024-12-16", "breaks": [("Fall Break", "2024-10-11", "2024-10-15"), ("Thanksgiving", "2024-11-26", "2024-11-30")]},
    {"name": "Spring 2025", "start": "2025-01-08", "end": "2025-05-03", "breaks": [("Spring Break", "2025-03-07", "2025-03-16")]},
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
        if 'breaks' in term:
            term['breaks'] = [(name, datetime.strptime(start, "%Y-%m-%d"), datetime.strptime(end, "%Y-%m-%d")) for name, start, end in term['breaks']]

    # Find the current term
    for term in terms:
        if term['start'] <= current_date <= term['end']:
            days_elapsed = (current_date - term['start']).days
            return term['start'], term['end'], days_elapsed, term['name'], term.get('breaks', [])

    # If not within any term, find the next upcoming term
    future_terms = [term for term in terms if term['start'] > current_date]
    if future_terms:
        next_term = min(future_terms, key=lambda term: term['start'])
        return next_term['start'], next_term['end'], 0, next_term['name'], next_term.get('breaks', [])

    # If no current or future term is found, return placeholders
    return None, None, 0, "No Active Term", []

# Function to calculate days remaining, considering breaks
def calculate_days_remaining(end_date, start_date, break_selection, current_date):
    days_remaining = (end_date - current_date).days
    adjusted_days_elapsed = (current_date - start_date).days
    
    # Adjust days_elapsed and days_remaining based on breaks
    for break_name, break_start, break_end, days_included in break_selection:
        break_start_date = break_start.date()  # Convert to date object
        break_end_date = break_end.date()  # Convert to date object
        break_duration = (break_end_date - break_start_date).days + 1
        if break_start_date > current_date:
            # Before the break, reduce future days
            days_remaining -= break_duration - days_included
        elif break_end_date < current_date:
            # After the break, deduct days from elapsed days
            adjusted_days_elapsed -= break_duration - days_included
    
    return days_remaining, adjusted_days_elapsed


# Get term dates
term_start_date, term_end_date, days_elapsed, term_name, breaks = get_term_dates()

# Streamlit UI
st.title("Food Point Calculator")
st.markdown(f"### {term_name}")

if term_start_date is None or term_end_date is None:
    st.error("Could not determine the current term dates.")
else:
    start_date = st.date_input("Start Date", term_start_date)
    end_date = st.date_input("End Date", term_end_date)

    if end_date < start_date:
        st.error("End date cannot be before start date.")
    else:
        plan_selected = st.selectbox("Select a Dining Plan", list(dining_plans.keys()))
        starting_points = st.number_input("Starting Food Points", value=dining_plans[plan_selected] if dining_plans[plan_selected] is not None else 0, min_value=0)

        if 'current_points' not in st.session_state:
            st.session_state.current_points = starting_points

        # Break selection
        break_selection = []
        if breaks:
            st.markdown("#### Breaks")
            for break_name, break_start, break_end in breaks:
                days_included = st.slider(f"How many days to include from {break_name}?", 0, (break_end - break_start).days + 1, (break_end - break_start).days + 1)
                break_selection.append((break_name, break_start, break_end, days_included))

        st.number_input("Current Food Points", min_value=0, key='current_points')

        # Calculate days remaining and adjusted days elapsed considering breaks
        days_remaining, adjusted_days_elapsed = calculate_days_remaining(end_date, start_date, break_selection, datetime.now().date())

        # Calculate points used and needed per day
        points_used = starting_points - st.session_state.current_points
        points_per_day_used = points_used / adjusted_days_elapsed if adjusted_days_elapsed > 0 else 0
        points_per_day_from_now = st.session_state.current_points / days_remaining if days_remaining > 0 else 0
        over_under = st.session_state.current_points - days_remaining * points_per_day_used

        # Display the results
        st.write(f"Days elapsed: {adjusted_days_elapsed}")
        st.write(f"Total days in term: {(end_date - start_date).days}")
        if adjusted_days_elapsed < 0: 
            st.write(f"You are able to spend {starting_points / (end_date - start_date).days:.2f} food points per day once the term begins.")
            st.write(f"Additional statistics on food points and current trajectory will appear after the term begins on {start_date}.")
        else:
            st.write(f"Points used so far: {points_used}")
            st.write(f"Average points used per day: {points_per_day_used:.2f}")
            st.write(f"Allowed points to spend per day from now on: {points_per_day_from_now:.2f}")
            st.write(f"Food points remaining if current trajectory continues: {over_under:.2f}")
