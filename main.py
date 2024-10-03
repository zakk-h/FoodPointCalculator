import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
import numpy as np
#from mabwiser.mab import MAB
from mabwiser.mab import MAB, LearningPolicy
import ast
#from mabwiser.linear import LinUCB
import logging
# Define the scope of access
scope = ["https://spreadsheets.google.com/feeds", 
         "https://www.googleapis.com/auth/drive"]

# Read credentials from the secrets.toml file
creds_dict = st.secrets["google_credentials"]

# Authenticate using the credentials from the secrets
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Open the Google Sheet by its URL
spreadsheet_url = "https://docs.google.com/spreadsheets/d/16uDILn_5phMRGMWVqTd6fnNf2q6XsZrnE7xQSZjnalY/edit?usp=sharing"
sheet = client.open_by_url(spreadsheet_url).worksheet("Data")

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

# Duke seems to be giving an additional 7.5% in food points for the Fall 2024 semester.
INFLATE = True

# Apply inflation if INFLATE is True
if INFLATE:
    for key in dining_plans:
        if dining_plans[key] is not None:
            dining_plans[key] = round(dining_plans[key] * 1.075)

# Hardcoded term dates and breaks for 2024-2026
terms = [
    # 2024-2025 Academic Year
    {"name": "Summer 2024 - Session 1", "start": "2024-05-15", "end": "2024-06-27"},
    {"name": "Summer 2024 - Session 2", "start": "2024-07-01", "end": "2024-08-11"},
    {"name": "Fall 2024", "start": "2024-08-26", "end": "2024-12-16", "breaks": [("Fall Break", "2024-10-11", "2024-10-15"), ("Thanksgiving", "2024-11-26", "2024-11-30")]},
    {"name": "Spring 2025", "start": "2025-01-08", "end": "2025-05-03", "breaks": [("Spring Break", "2025-03-07", "2025-03-16")]},
    {"name": "Summer 2025 - Session 1", "start": "2025-05-14", "end": "2025-06-26"},
    {"name": "Summer 2025 - Session 2", "start": "2025-06-30", "end": "2025-08-11"},

    # 2025-2026 Academic Year
    {"name": "Summer 2025 - Session 1", "start": "2025-05-14", "end": "2025-06-26"},
    {"name": "Summer 2025 - Session 2", "start": "2025-06-30", "end": "2025-08-11"},
    {"name": "Fall 2025", "start": "2025-08-25", "end": "2025-12-15", "breaks": [("Fall Break", "2025-10-10", "2025-10-15"), ("Thanksgiving", "2025-11-25", "2025-11-30")]},
    {"name": "Spring 2026", "start": "2026-01-07", "end": "2026-05-02", "breaks": [("Spring Break", "2026-03-06", "2026-03-16")]},
    {"name": "Summer 2026 - Session 1", "start": "2026-05-13", "end": "2026-06-25"},
    {"name": "Summer 2026 - Session 2", "start": "2026-06-29", "end": "2026-08-10"}
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

def log_to_google_sheets(data):
    # Append the data to the spreadsheet
    sheet.append_row(data)

def get_or_create_bandit_sheet(client, spreadsheet_url):
    try:
        return client.open_by_url(spreadsheet_url).worksheet("Bandit")
    except gspread.exceptions.WorksheetNotFound:
        bandit_sheet = client.open_by_url(spreadsheet_url).add_worksheet(title="Bandit", rows="1000", cols="20")
        bandit_sheet.append_row(["Username", "Day", "Hour", "Action", "Reward"])
        return bandit_sheet

@st.cache_resource
def initialize_bandit(actions):
    return MAB(arms=actions, learning_policy=LearningPolicy.LinUCB(alpha=1.0), neighborhood_policy=None)

def food_suggestion():
    st.title("Food Suggestion")
    username = st.text_input("Enter your username")

    # Initialize session state variables
    if 'suggested_action' not in st.session_state:
        st.session_state.suggested_action = None
    if 'rating_submitted' not in st.session_state:
        st.session_state.rating_submitted = False

    if username:
        try:
            bandit_sheet = get_or_create_bandit_sheet(client, spreadsheet_url)
            data = bandit_sheet.get_all_values()
            headers = data[0]  # Assuming first row is the header
            data_rows = data[1:]  # Data excluding the header
            df = pd.DataFrame(data_rows, columns=headers)

            # Normalize username for case-insensitive matching
            df = df[df['Username'].str.lower() == username.lower()]
            if df.empty:
                user_data = pd.DataFrame(columns=['Username', 'Day', 'Hour', 'Action', 'Reward'])
            else:
                df['Day'] = df['Day'].astype(int)
                df['Hour'] = df['Hour'].astype(int)
                df['Reward'] = df['Reward'].astype(float)
                user_data = df

            actions = [
                "Chicken Parmesan Panini",
                "Chicken Pesto Panini",
                "French Beef Panini",
                "Fried Chicken Pimiento Cheese Panini",
                "Grilled Ratatouille Panini",
                "The Toscana",
                "Greek Salad",
                "Salmon Bowl",
                "Salmon Garden Salad",
                "Southwest Chicken Bowl",
                "Vegan Buddah Bowl",
                "Classic Lasagna",
                "Gourmet Mac N Cheese",
                "Tomato Basil Bisque",
                "Apple Moroccan Couscous",
                "Chicken Salad Snack Box",
                "Farm Fresh Eggs",
                "Feta Cilantro Bowtie Salad",
                "Fruit Cup",
                "Garbanzo Greek Salad",
                "Hummus and Pita Crisp",
                "Hummus and Pita Cup",
                "Mediterranean Snack Box",
                "Penne Pesto Salad",
                "Pita Crisps",
                "Strawberry Fruit Cup",
                "Turkey Snack Box",
                "Buffalo Chicken Pita",
                "Chicken Arugula Sandwich",
                "Chicken Salad Brioche",
                "Chicken Salad Croissant",
                "Chicken Shawarma",
                "Falafel on Pita",
                "Hummus Veggie Wrap",
                "Southwest Chicken Wrap",
                "Southwest Turkey Wrap",
                "Apple and Brie Crepe",
                "Chicken Pesto Crepe",
                "Croque Monsieur Crepe",
                "Florentine Crepe",
                "Banana",
                "Homemade Whipped Cream",
                "Strawberry",
                "Black and White Cookie",
                "Cheesecake Brownie",
                "Chocolate Chip Cookie",
                "Death by Chocolate Cake",
                "Frosted Chocolate Cupcake",
                "Frosted Cookies and Cream Cupcake",
                "Frosted Strawberry Lemonade Cupcake",
                "Frosted Vanilla Cupcake",
                "Fudge Brownie",
                "Lemon Bar",
                "Lemon Pound Cake",
                "Oatmeal Raisin Cookies",
                "Pumpkin Sweet Bread",
                "Shortdough Cookie",
                "Strawberry Shortcake Cake",
                "Tiramisu Cake",
                "Cappucino Gelato",
                "Chocolate Gelato",
                "Dulce de Leche Gelato",
                "Lemon Sorbet",
                "Mango Sorbet",
                "Mint Chocolate Chip Gelato",
                "Mixed Berry Sorbet",
                "Pomegranate Orange Blossom Gelato",
                "Salted Caramel Gelato",
                "Vanilla Gelato"
            ]

            now = datetime.now()
            day_of_week = now.weekday()
            hour_of_day = now.hour

            # Initialize the bandit model
            mab = initialize_bandit(actions)

            # Extract historical actions, rewards, and contexts
            if not user_data.empty:
                actions_taken = user_data['Action'].tolist()
                rewards = user_data['Reward'].tolist()
                contexts = user_data[['Day', 'Hour']].values.tolist()
            else:
                actions_taken = []
                rewards = []
                contexts = []

            # Generate a new suggestion only if one hasn't been made or has been reset
            if st.session_state.suggested_action is None:
                if len(actions_taken) >= 10:
                    mab.fit(actions_taken, rewards, contexts)
                    current_context = [[day_of_week, hour_of_day]]
                    suggested_action = mab.predict(current_context)
                else:
                    st.warning(f"Insufficient data to train the model. (only {len(actions_taken)} actions so far). Providing a random suggestion.")
                    suggested_action = np.random.choice(actions)

                st.session_state.suggested_action = suggested_action
                st.session_state.rating_submitted = False  # Reset submission flag for new suggestion

            suggested_action = st.session_state.suggested_action

            st.write(f"**Suggested food for you:** {suggested_action}")

            with st.form(key='rating_form'):
                rating = st.slider("How would you rate this suggestion?", 1, 5, 3)
                submit_button = st.form_submit_button(label='Submit Rating')

            if submit_button and not st.session_state.rating_submitted:
                # Append the new rating to the Google Sheet
                new_row = [username, str(day_of_week), str(hour_of_day), suggested_action, str(rating)]
                bandit_sheet.append_row(new_row)

                st.success("Thank you for your feedback!")

                # Update session state to reflect that rating has been submitted
                st.session_state.rating_submitted = True

            elif st.session_state.rating_submitted:
                st.info("You have already submitted a rating for this suggestion.")

            # Provide a button to get a new suggestion after submission
            if st.session_state.rating_submitted:
                if st.button("Get a New Suggestion"):
                    st.session_state.suggested_action = None
                    st.session_state.rating_submitted = False
                    st.rerun()  # Rerun the script to generate a new suggestion

        except gspread.exceptions.APIError as api_err:
            st.error(f"Google Sheets API error: {api_err}")
        except ValueError as val_err:
            st.error(f"Data processing error: {val_err}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
    else:
        st.info("Please enter your username to get a food suggestion.")


def food_point_calculator():
    # Get term dates
    term_start_date, term_end_date, days_elapsed, term_name, breaks = get_term_dates()

    # Streamlit UI
    st.title("Food Point Calculator")
    st.markdown(f"### {term_name}")

    if term_start_date is None or term_end_date is None:
        st.error("Could not determine the current term dates.")
    else:
        start_date = st.date_input("Start Date", term_start_date-timedelta(days=2)) # People traditionally move in on Saturday
        end_date = st.date_input("End Date", term_end_date)

        if end_date < start_date:
            st.error("End date cannot be before start date.")
        else:
            plan_selected = st.selectbox("Select a Dining Plan", list(dining_plans.keys()))
            starting_points = st.number_input("Starting Food Points", value=dining_plans[plan_selected] if dining_plans[plan_selected] is not None else 0, min_value=0)

            if 'current_points' not in st.session_state:
                st.session_state.current_points = starting_points

            st.number_input("Current Food Points", min_value=0, key='current_points')

            # Break selection
            break_selection = []
            total_days_in_term = (end_date - start_date).days
            days_present = total_days_in_term  # Initially assume the user is present for all days
            
            if breaks:
                st.markdown("#### Breaks")
                for break_name, break_start, break_end in breaks:
                    # Determine if the break has already happened
                    current_date = datetime.now().date()
                    if break_end.date() < current_date:
                        verb = "were"
                    else:
                        verb = "are"

                    days_included = st.slider(
                                f"How many days were you here during {break_name}?", 
                                0, 
                                (break_end - break_start).days + 1, 
                                0  # Default value set to 0
                    )
                    break_selection.append((break_name, break_start, break_end, days_included))
                    break_duration = (break_end - break_start).days + 1
                    days_present -= (break_duration - days_included)

            # Calculate days remaining and adjusted days elapsed considering breaks
            days_remaining, adjusted_days_elapsed = calculate_days_remaining(end_date, start_date, break_selection, datetime.now().date())

            # Calculate points used and needed per day
            points_used = starting_points - st.session_state.current_points
            points_per_day_used = points_used / adjusted_days_elapsed if adjusted_days_elapsed > 0 else 0
            points_per_day_from_now = st.session_state.current_points / days_remaining if days_remaining > 0 else 0
            over_under = st.session_state.current_points - days_remaining * points_per_day_used

            # Display the results
            st.write(f"Days elapsed: {adjusted_days_elapsed}")
            st.write(f"Total days in term: {total_days_in_term} (Days present: {days_present})")
            if adjusted_days_elapsed < 0: 
                st.write(f"You are able to spend {starting_points / days_present:.2f} food points per day once the term begins.")
                st.write(f"Additional statistics on food points and current trajectory will appear after the term begins on {start_date}.")
            else:
                # Log data to Google Sheets
                break_data = [days_included for _, _, _, days_included in break_selection]  # Extract days included for each break
                log_data = [
                                starting_points, 
                                st.session_state.current_points, 
                                start_date.strftime('%Y-%m-%d'), 
                                end_date.strftime('%Y-%m-%d'), 
                                datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
                            ] + break_data
                log_to_google_sheets(log_data)

                st.write(f"Points used so far: {points_used}")
                st.write(f"Average points used per day: {points_per_day_used:.2f}")
                st.write(f"Allowed points to spend per day from now on: {points_per_day_from_now:.2f}")
                st.write(f"Food points remaining if current trajectory continues: {over_under:.2f}")

                # Plot the food points projection
                dates_so_far = np.array([start_date + timedelta(days=i) for i in range(adjusted_days_elapsed + 1)])
                dates_remaining = np.array([start_date + timedelta(days=adjusted_days_elapsed + i) for i in range(days_remaining + 1)])

                # Points arrays based on the calculated slopes
                points_so_far = starting_points - points_per_day_used * np.arange(adjusted_days_elapsed + 1)
                points_projected = st.session_state.current_points - points_per_day_used * np.arange(days_remaining + 1)
                points_required = st.session_state.current_points - points_per_day_from_now * np.arange(days_remaining + 1)

                # Multi-line comments are intepreted as strings in Streamlit and displayed in the app
                # Plotting
                #plt.figure(figsize=(10, 6))

                # Plot the actual points spent so far
                #plt.plot(dates_so_far, points_so_far, label="Points Spent So Far", color='blue')

                # Plot the projected spending if current rate continues
                #plt.plot(dates_remaining, points_projected, label="Current Spending Projection", linestyle='--', color='blue')

                # Plot the optimal spending to finish at zero points
                #plt.plot(dates_remaining, points_required, label="Average Spending to Finish at 0", color='red')

                # Add labels and legend
                #plt.xlabel("Date")
                #plt.ylabel("Food Points")
                #plt.title("Food Points Spending Projection")
                #plt.legend()

                # Display plot in Streamlit
                #st.pyplot(plt)
                
                # Combine all data into a DataFrame
                df_so_far = pd.DataFrame({'Date': dates_so_far, 'Points': points_so_far, 'Type': 'Points Spent So Far'})
                df_projected = pd.DataFrame({'Date': dates_remaining, 'Points': points_projected, 'Type': 'Current Spending Projection'})
                df_required = pd.DataFrame({'Date': dates_remaining, 'Points': points_required, 'Type': 'Average Spending to Finish at 0'})

                # Concatenate dataframes
                df_all = pd.concat([df_so_far, df_projected, df_required])

                # Plot using Streamlit's built-in chart functionality
                st.line_chart(df_all.pivot(index='Date', columns='Type', values='Points'))

                st.markdown('<p style="font-size: 9px; color: gray;">Note: Data entered is stored for cohort analysis purposes.</p>', unsafe_allow_html=True)


# Streamlit UI
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Food Point Calculator", "Food Suggestion"])
if page == "Food Point Calculator":
    food_point_calculator()
elif page == "Food Suggestion":
    food_suggestion()