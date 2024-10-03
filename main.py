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

#def get_or_create_bandit_sheet(client, spreadsheet_url):
#    try:
#        return client.open_by_url(spreadsheet_url).worksheet("Bandit")
#    except gspread.exceptions.WorksheetNotFound:
#        bandit_sheet = client.open_by_url(spreadsheet_url).add_worksheet(title="Bandit", rows="1000", cols="20")
#        bandit_sheet.append_row(["Username", "Day", "Hour", "Action", "Reward"])
#        return bandit_sheet
#def get_or_create_bandit_sheet(client, spreadsheet_url, username):
#    sheet_name = f"Bandits_{username.lower()}"
#    try:
#        return client.open_by_url(spreadsheet_url).worksheet(sheet_name)
#    except gspread.exceptions.WorksheetNotFound:
#        # Create the user's own bandit sheet if not found
#        bandit_sheet = client.open_by_url(spreadsheet_url).add_worksheet(title=sheet_name, rows="1000", cols="20")
#        bandit_sheet.append_row(["Username", "Day", "Hour", "Action", "Reward"])
#        return bandit_sheet
def get_or_create_bandit_sheet(client, spreadsheet_url, username):
    sheet_name = f"Bandits_{username.lower()}"
    try:
        return client.open_by_url(spreadsheet_url).worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        bandit_sheet = client.open_by_url(spreadsheet_url).add_worksheet(title=sheet_name, rows="1000", cols="20")
        bandit_sheet.append_row(["Username", "Day", "Hour", "Category", "Item", "Reward"])
        return bandit_sheet

def get_menu():
    # Define the food categories and items
    food_categories = {
        "Paninis & Sandwiches": [
            "Cafe Chicken Parmesan Panini", 
            "Cafe Chicken Pesto Panini", 
            "Cafe French Beef Panini", 
            "Cafe Fried Chicken Pimiento Cheese Panini", 
            "Cafe Grilled Ratatouille Panini", 
            "Cafe The Toscana", 
            "Cafe Buffalo Chicken Pita", 
            "Cafe Chicken Arugula Sandwich", 
            "Cafe Chicken Salad Brioche", 
            "Cafe Chicken Salad Croissant", 
            "Cafe Chicken Shawarma", 
            "Cafe Falafel on Pita", 
            "Cafe Hummus Veggie Wrap", 
            "Cafe Southwest Chicken Wrap", 
            "Cafe Southwest Turkey Wrap", 
            "Gothic Grill BLT-A Sandwich", 
            "Gothic Grill Calabash Fish Sandwich", 
            "Gothic Grill Chicken and Fresh Mozzarella Sandwich", 
            "Gothic Grill Chicken Parmesan Sandwich", 
            "Gothic Grill Philly Cheesesteak Sandwich", 
            "Gothic Grill Grilled Chicken Sandwich", 
            "Gothic Grill Pastrami Reuben Sandwich", 
            "Gyotaku Arctic Sushi Burrito", 
            "Gyotaku Atlantic Sushi Burrito", 
            "Gyotaku Indian Sushi Burrito", 
            "Gyotaku Pacific Sushi Burrito", 
            "Gyotaku Southern Sushi Burrito",
            "Red Mango Chicken Caesar Wrap", 
            "Red Mango Chicken Salad Wrap", 
            "Red Mango Ham and Provolone Wrap", 
            "Red Mango Tuna Salad Wrap", 
            "Red Mango Turkey and Provolone Wrap", 
            "Sprout Avocado Toast", 
            "Sprout Black Bean Burger Sandwich", 
            "Sprout Falafel Wrap", 
            "The Farmstead Bratwurst with Onion and Pepper Sandwich", 
            "The Farmstead Chicken Caesar Salad Wrap", 
            "The Farmstead Farmstead Chicken Shawarma Wrap", 
            "The Farmstead Farmstead Lamb Gyro", 
            "The Farmstead Ham and Cheddar Sandwich", 
            "The Farmstead Kobe Beef Sliders", 
            "The Farmstead Salmon Burger with Bun", 
            "The Farmstead Turkey and Swiss Sandwich", 
            "The Farmstead Turkey Avocado Sandwich", 
            "Zweli's Buffalo Chicken Panini", 
            "Zweli's Garden Veggie Panini", 
            "Zweli's Italian Panini", 
            "Zweli's Turkey Avocado Panini",
            "Zweli's Grilled Cheese Sandwich", 
        ],
        
        "Salads & Bowls": [
            "Cafe Greek Salad", 
            "Cafe Salmon Bowl", 
            "Cafe Salmon Garden Salad", 
            "Cafe Southwest Chicken Bowl", 
            "Cafe Vegan Buddah Bowl", 
            "Ginger and Soy Every Day Poke Bowl", 
            "Ginger and Soy California Bowl", 
            "Ginger and Soy Hong Kong Bowl", 
            "Ginger and Soy Seoul Bowl", 
            "Ginger and Soy Shanghai Bowl", 
            "Ginger and Soy Tokyo Bowl", 
            "J.B.'s Roast and Chops Apple Fennel Salad", 
            "J.B.'s Roast and Chops Caesar Salad", 
            "J.B.'s Roast and Chops Smoked Chophouse Salad", 
            "Gothic Grill Caesar Salad", 
            "Gothic Grill Caprese Grilled Chicken Salad", 
            "Gothic Grill Crispy Buffalo Chicken Salad", 
            "Red Mango Berries and Acai Bowl", 
            "Red Mango Choc-Nut Dream Bowl", 
            "Red Mango Honey Apple Bowl", 
            "Red Mango PB Power Bowl", 
            "Red Mango Red White and Blue Bowl", 
            "Red Mango The Pink Bowl", 
            "Red Mango Totally Tropical Bowl", 
            "Sprout Arugula Chicken and Goat Cheese Salad", 
            "Sprout Caribbean Fish Salad", 
            "Sprout Flank Steak Salad", 
            "Sprout Fried Chicken Salad", 
            "Sprout Ginger Salmon Salad", 
            "Sprout Mixed Arugula Salad", 
            "Sprout Southwest Chicken Cobb Salad", 
            "Sazon Arepa Bowl", 
            "Devil's Krafthouse Buffalo Bacon Ranch Bowl"
        ],
        
        "Pasta & Pizza": [
            "Cafe Classic Lasagna", 
            "Cafe Gourmet Mac N Cheese", 
            "Il Forno Blackened Shrimp Scampi", 
            "Il Forno Braised Italian Beef Pasta", 
            "Il Forno Chicken Alfredo Pasta", 
            "Il Forno Chicken Basil Pesto Pasta", 
            "Il Forno Garden Veggie Pasta", 
            "Il Forno Meatball and Spaghetti Pasta", 
            "Il Forno Parma Rosa Pasta", 
            "Il Forno Salmon Alfredo Pasta", 
            "Il Forno Spicy IL Forno Pasta", 
            "Il Forno Blaise Pizza", 
            "Il Forno Bruschetta Pizza", 
            "Il Forno Buffalo Chicken Pizza", 
            "Il Forno Cheese Pizza", 
            "Il Forno Four Cheese Pizza", 
            "Il Forno Margherita Pizza", 
            "Il Forno Pepperoni Pizza", 
            "PJ's New Yorker Pizza", 
            "PJ's Quattro Pizza", 
            "PJ's Rustic Pizza", 
            "PJ's Stinger Pizza"
        ],
        
        "Dumplings & Spring Rolls": [
            "Ginger and Soy Beef Dumplings", 
            "Ginger and Soy Chicken Dumplings", 
            "Ginger and Soy Vegetable Dumpling", 
            "Ginger and Soy Vegetable Spring Roll"
        ],
        
        "Snacks & Sides": [
            "Cafe Chicken Salad Snack Box", 
            "Cafe Apple Moroccan Couscous", 
            "Cafe Hummus and Pita Crisp", 
            "Cafe Mediterranean Snack Box", 
            "Cafe Penne Pesto Salad", 
            "Cafe Pita Crisps", 
            "Cafe Turkey Snack Box", 
            "Gothic Grill Buffalo Chicken Macaroni and Cheese", 
            "Gothic Grill Chicken Cheese Nachos", 
            "Gothic Grill Chicken Tenders", 
            "Gothic Grill Chicken Wings", 
            "Gothic Grill Crispy Cauliflower", 
            "Gothic Grill Fried Shrimp", 
            "Gothic Grill Mozzarella Sticks", 
            "Gothic Grill Sweet Potato Waffle Fries", 
            "Gothic Grill Zucchini Fries", 
            "J.B.'s Roast and Chops Flourless Chocolate Torte", 
            "J.B.'s Roast and Chops Tiramisu", 
            "J.B.'s Roast and Chops White Chocolate Raspberry Cheesecake", 
            "Red Mango Blueberry Fruit Cup", 
            "Red Mango Coconut Chia Blueberry Pudding Parfait", 
            "Red Mango Strawberry Fruit Cup", 
            "Red Mango Strawberry Coconut Chia Pudding Parfait", 
            "Red Mango Yogurt Parfait w/ Blueberry & Strawberry", 
            "Sprout Balsamic Maple Brussels Sprouts", 
            "Sprout Brown Rice", 
            "Sprout Pita Bread", 
            "Devil's Krafthouse Barbecue Ranch Fries", 
            "Devil's Krafthouse Battered Dill Pickle Chips", 
            "Devil's Krafthouse Battered Onion Rings", 
            "Devil's Krafthouse Buffalo Ranch Chicken Fries", 
            "Devil's Krafthouse Cheese Curds", 
            "Devil's Krafthouse Fresh Cut Fries", 
            "Devil's Krafthouse House Made Chips", 
            "Devil's Krafthouse Loaded Chips", 
            "Devil's Krafthouse Loaded Fries", 
            "Devil's Krafthouse Loaded Sweet Potato Tots", 
            "Devil's Krafthouse Nachos", 
            "Devil's Krafthouse Sweet Potato Tots", 
            "Devil's Krafthouse Tempura Brussel Sprouts", 
            "Devil's Krafthouse Vegan Crispy Garden Tenders"
        ],
        
        "Desserts & Pastries": [
            "Cafe Black and White Cookie", 
            "Cafe Cheesecake Brownie", 
            "Cafe Chocolate Chip Cookie", 
            "Cafe Death by Chocolate Cake", 
            "Cafe Frosted Chocolate Cupcake", 
            "Cafe Frosted Cookies and Cream Cupcake", 
            "Cafe Frosted Strawberry Lemonade Cupcake", 
            "Cafe Frosted Vanilla Cupcake", 
            "Cafe Fudge Brownie", 
            "Cafe Lemon Bar", 
            "Cafe Lemon Pound Cake", 
            "Cafe Oatmeal Raisin Cookies", 
            "Cafe Pumpkin Sweet Bread", 
            "Cafe Shortdough Cookie", 
            "Cafe Strawberry Shortcake Cake", 
            "Cafe Tiramisu Cake", 
            "Gothic Grill Banana Split", 
            "Gothic Grill Browndae Sundae", 
            "Gothic Grill Chocolate Diablo Sundae", 
            "Gothic Grill Dirt and Worms Sundae", 
            "Red Mango Chocolate Chip Power Bites", 
            "Red Mango Double Chocolate Power Bites", 
            "Sprout Spanakopita Spinach Pie", 
            "Devil's Krafthouse Cappuccino Chip Sundae", 
            "Devil's Krafthouse Ice Cream Nachos", 
            "Devil's Krafthouse Ice Cream Sandwich", 
            "Devil's Krafthouse Nacho Sundae", 
            "Devil's Krafthouse Oreo Mint Sundae", 
            "Devil's Krafthouse Oreo Sundae", 
            "Devil's Krafthouse Strawberry Chip Sundae", 
            "Devil's Krafthouse Strawberry Sundae", 
            "Devil's Krafthouse Triple Chocolate Sundae"
        ],
        
        "Gelato & Ice Cream": [
            "Cafe Cappuccino Gelato", 
            "Cafe Chocolate Gelato", 
            "Cafe Dulce de Leche Gelato", 
            "Cafe Lemon Sorbet", 
            "Cafe Mango Sorbet", 
            "Cafe Mint Chocolate Chip Gelato", 
            "Cafe Mixed Berry Sorbet", 
            "Cafe Pomegranate Orange Blossom Gelato", 
            "Cafe Salted Caramel Gelato", 
            "Cafe Vanilla Gelato", 
            "Gothic Grill Chocolate Cookie Dough Ice Cream", 
            "Gothic Grill Chocolate Ice Cream", 
            "Gothic Grill Coffee Ice Cream", 
            "Gothic Grill Cookies and Cream Ice Cream", 
            "Gothic Grill Devil's Delight Ice Cream", 
            "Gothic Grill Mint Chocolate Chip Ice Cream", 
            "Gothic Grill Strawberry Ice Cream", 
            "Gothic Grill Vanilla Ice Cream"
        ],
        
        "Seafood": [
            "Gyotaku Blossom Roll", 
            "Gyotaku California Roll", 
            "Gyotaku Coco Roll", 
            "Gyotaku Dancing Eel Roll", 
            "Gyotaku Fire Cracker Roll", 
            "Gyotaku Gyotaku Special Roll", 
            "Gyotaku Mary Roll", 
            "Gyotaku Rainbow Roll", 
            "Gyotaku Red Dragon Roll", 
            "Gyotaku Salmon Avocado Roll", 
            "Gyotaku Salmon Crunch Roll", 
            "Gyotaku Shrimp Tempura Roll", 
            "Gyotaku Spicy Tuna Crunch Roll", 
            "Gyotaku Veggie Roll", 
            "Gyotaku White Tiger Roll", 
            "J.B.'s Roast and Chops Grilled Salmon", 
            "J.B.'s Roast and Chops Grilled Yellow Fin Tuna", 
            "J.B.'s Roast and Chops Shrimp Skewer", 
            "The Farmstead Atlantic Blackened Salmon Fillets", 
            "The Farmstead Salmon Burger with Bun"
        ],
        
        "Soups": [
            "Gothic Grill Broccoli and Cheese Soup", 
            "Gothic Grill Chicken and Noodle Soup", 
            "Gothic Grill Chicken Tortilla Soup", 
            "Gothic Grill House Chili Soup", 
            "Gothic Grill Tomato Basil Soup", 
            "Gothic Grill Vegan Vegetable Soup"
        ],
        
        "Burgers": [
            "Gothic Grill Black Bean Burger Sandwich", 
            "Gothic Grill Double Patty Melt Sandwich", 
            "Gothic Grill Duke Bleu Cheese Burger", 
            "Gothic Grill Gothic Burger", 
            "Gothic Grill NC Burger", 
            "Devil's Krafthouse BBQ Bacon Burger", 
            "Devil's Krafthouse Brecky Burger", 
            "Devil's Krafthouse Brie and Bacon Jam Burger", 
            "Devil's Krafthouse Diablo Burger", 
            "Devil's Krafthouse Dilly Burger", 
            "Devil's Krafthouse Impossible Burger", 
            "Devil's Krafthouse Krafthouse Burger", 
            "Devil's Krafthouse Loaded Pastrami Burger", 
            "Devil's Krafthouse Mushroom Swiss Burger", 
            "Devil's Krafthouse Queso Burger"
        ],

        "Lunch Entrees": [
            "Zweli's Curry Chicken", 
            "Zweli's Grilled Portabella Mushroom", 
            "Zweli's Honey Glazed Pork Chop", 
            "Zweli's Nyama Zimbabwean Beef Stew", 
            "Zweli's Piri Piri Grilled Chicken Breast", 
            "Tandoor Beef Aloo", 
            "Tandoor Chicken 65", 
            "Tandoor Chicken Curry", 
            "Tandoor Chicken Tikka Masala", 
            "Tandoor Malabar Fish", 
            "Tandoor Chana Masala", 
            "Tandoor Curry Egg", 
            "Tandoor Mixed Vegetables", 
            "Tandoor Panir Saag", 
            "Tandoor Tofu Tikka Masala"
        ]
    }
    return food_categories


#@st.cache_resource
#def initialize_bandit(actions):
#    return MAB(arms=actions, learning_policy=LearningPolicy.LinUCB(alpha=1.0), neighborhood_policy=None)

@st.cache_resource
def initialize_bandits(categories):
    category_bandit = MAB(
        arms=list(categories.keys()),
        learning_policy=LearningPolicy.LinUCB(alpha=1.0),
        neighborhood_policy=None
    )
    
    item_bandits = {category: MAB(arms=items, learning_policy=LearningPolicy.LinUCB(alpha=1.0), neighborhood_policy=None)
                    for category, items in categories.items()}
    return category_bandit, item_bandits


def food_suggestion():
    st.title("Food Suggestion")
    username = st.text_input("Enter your username")

    food_categories = get_menu()

    if 'suggested_category' not in st.session_state:
        st.session_state.suggested_category = None
    if 'suggested_item' not in st.session_state:
        st.session_state.suggested_item = None
    if 'rating_submitted' not in st.session_state:
        st.session_state.rating_submitted = False

    if username:
        try:
            bandit_sheet = get_or_create_bandit_sheet(client, spreadsheet_url, username)
            data = bandit_sheet.get_all_values()
            headers = data[0]
            data_rows = data[1:]
            df = pd.DataFrame(data_rows, columns=headers)
            df = df[df['Username'].str.lower() == username.lower()]

            now = datetime.now()
            day_of_week = now.weekday()
            hour_of_day = now.hour

            # Initialize bandits
            category_bandit, item_bandits = initialize_bandits(food_categories)

            # Train category-level bandit
            if not df.empty:
                category_actions = df['Category'].tolist()
                rewards = df['Reward'].astype(float).tolist()
                contexts = df[['Day', 'Hour']].astype(int).values.tolist()

                if len(category_actions) >= 10:
                    category_bandit.fit(category_actions, rewards, contexts)

            # Predict category
            if st.session_state.suggested_category is None:
                if len(df) >= 10:
                    suggested_category = category_bandit.predict([[day_of_week, hour_of_day]])
                else:
                    suggested_category = np.random.choice(list(food_categories.keys()))
                st.session_state.suggested_category = suggested_category
                st.session_state.rating_submitted = False

            suggested_category = st.session_state.suggested_category

            # Train item-level bandit
            df_category = df[df['Category'] == suggested_category]
            if not df_category.empty:
                item_actions = df_category['Item'].tolist()
                item_rewards = df_category['Reward'].astype(float).tolist()
                item_contexts = df_category[['Day', 'Hour']].astype(int).values.tolist()

                if len(item_actions) >= 5:
                    item_bandits[suggested_category].fit(item_actions, item_rewards, item_contexts)

            # Predict item
            if st.session_state.suggested_item is None:
                if len(df_category) >= 5:
                    suggested_item = item_bandits[suggested_category].predict([[day_of_week, hour_of_day]])
                else:
                    suggested_item = np.random.choice(food_categories[suggested_category])
                st.session_state.suggested_item = suggested_item

            suggested_item = st.session_state.suggested_item

            st.write(f"**Suggested Category:** {suggested_category}")
            st.write(f"**Suggested Food Item:** {suggested_item}")

            with st.form(key='rating_form'):
                rating = st.slider("How would you rate this suggestion?", 1, 5, 3)
                submit_button = st.form_submit_button(label='Submit Rating')

            if submit_button and not st.session_state.rating_submitted:
                # Append the new rating to the Google Sheet
                new_row = [username, str(day_of_week), str(hour_of_day), suggested_category, suggested_item, str(rating)]
                bandit_sheet.append_row(new_row)

                st.success("Thank you for your feedback!")
                st.session_state.rating_submitted = True

            elif st.session_state.rating_submitted:
                st.info("You have already submitted a rating for this suggestion.")

            if st.session_state.rating_submitted:
                if st.button("Get a New Suggestion"):
                    st.session_state.suggested_category = None
                    st.session_state.suggested_item = None
                    st.session_state.rating_submitted = False
                    st.rerun()

        except gspread.exceptions.APIError as api_err:
            st.error(f"Google Sheets API error: {api_err}")
        except ValueError as val_err:
            st.error(f"Data processing error: {val_err}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
    else:
        st.info("Please enter your username to get a food suggestion.")


def food_point_calculator():
    try:
        sheet = client.open_by_url(spreadsheet_url).worksheet("Data")
    except gspread.exceptions.WorksheetNotFound:
        st.error("The worksheet 'Data' was not found. Please check if it exists.")
    except gspread.exceptions.APIError as api_err:
        st.error(f"API error: {api_err}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

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