import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime

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

# Function to scrape the Duke academic calendar and determine the current term
def get_term_dates():
    url = "https://registrar.duke.edu/2024-2025-academic-calendar/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    current_date = datetime.now()
    term_start_date = None
    term_end_date = None

    # Find the term that includes today's date
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            columns = row.find_all('td')
            if columns and len(columns) >= 3:
                date_text = columns[0].text.strip().split('–')[0].strip()
                event = columns[2].text.strip().lower()

                # Determine the correct year for the date
                try:
                    month_day = datetime.strptime(date_text, '%B %d')
                    year = current_date.year if month_day.month >= current_date.month else current_date.year + 1
                    date = datetime.strptime(f"{date_text}, {year}", '%B %d, %Y')
                except ValueError:
                    continue  # Skip rows that don't match the expected date format

                if 'classes begin' in event and date <= current_date:
                    term_start_date = date

                if 'final examinations end' in event and term_start_date and not term_end_date:
                    term_end_date = date

    return term_start_date, term_end_date

# Get term dates
term_start_date, term_end_date = get_term_dates()

# Streamlit UI
st.title("Food Point Calculator")

if term_start_date is None or term_end_date is None:
    st.error("Could not determine the current term dates from the academic calendar.")
else:
    # Input fields for start date, end date, and selecting a dining plan
    start_date = st.date_input("Start Date", term_start_date)
    end_date = st.date_input("End Date", term_end_date)
    
    plan_selected = st.selectbox("Select a Dining Plan", list(dining_plans.keys()))
    starting_points = st.number_input("Starting Food Points", value=dining_plans[plan_selected] if dining_plans[plan_selected] is not None else 0, min_value=0)
    
    current_points = st.number_input("Current Food Points", min_value=0)

    # Calculate the days elapsed and total days in the term
    days_elapsed = (datetime.now().date() - start_date).days
    total_days = (end_date - start_date).days
    days_remaining = (end_date - datetime.now().date()).days
    
    # Calculate points used and needed per day
    points_used = starting_points - current_points
    points_per_day_used = points_used / days_elapsed if days_elapsed > 0 else 0
    points_per_day_total = starting_points / total_days if total_days > 0 else 0
    points_per_day_from_now = current_points / days_remaining if days_remaining > 0 else 0
    over_under = current_points - days_remaining*points_per_day_used

    # Display the results
    st.write(f"Days elapsed: {days_elapsed}")
    st.write(f"Total days in term: {total_days}")
    st.write(f"Points used so far: {points_used}")
    st.write(f"Average points used per day: {points_per_day_used:.2f}")
    st.write(f"Allowed points to spent per day from now on: {points_per_day_from_now:.2f}")
    st.write(f"Food points remaining if current trajectory continues: {over_under:.2f}")

