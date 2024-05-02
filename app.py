import streamlit as st
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Streamlit application title
st.title('API Programme - Clicks Fetcher')

# Authorization token
auth_token = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiIxODUyZmZmNi02N2RlLTRiNjYtYmIwMy01NDJlY2Q4YmZmNzMiLCJhZG0iOnRydWUsImlhdCI6MTcxNDY0MjU5MSwiZXhwIjoxNzE0NzI4OTkxLCJhdWQiOiJwbGF0bzowLjAuMSIsImlzcyI6InZhcnNpdHktbGl2ZSJ9.qCXRtC38BFCwvqEWO8FDax5aQO_uvGCwekEk8kiZc14'
headers = {'Authorization': auth_token}

# Function to fetch clicks data
def fetch_clicks(url, event_name):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()['items']
        return pd.DataFrame(data).assign(event_name=event_name)
    else:
        return pd.DataFrame()

# Default selections
default_events = [
    "apply_now", "curriculum_day1", "curriculum_day2", "date_filter",
    "date_selection", "join_session", "language_filter", "language_selection",
    "popup_cancel", "programme_card", "signin_initated"
]

# Fetch event names for dropdown
all_clicks_url = "https://oracle.varsitylive.in/admin/web-analytics/click/all"
all_clicks_response = fetch_clicks(all_clicks_url, "initial_load")
if all_clicks_response.empty:
    st.error("Error fetching event names.")
else:
    event_names = all_clicks_response['eventName'].unique()
    
   # Create three columns for the input selections
    col1, col2, col3 = st.columns(3)
    
    # Input for Event Name in the first column
    with col1:
        eventName = st.selectbox("Event Name", ('All', 'Click', 'Scroll'))
    
    # Input for Identifier Type in the second column
    with col2:
        identifierType = st.selectbox("Identifier Type", ('Program', 'genericid', 'faq category', 'faq question'))
    
    # Input for Duration in the third column
    with col3:
        duration = st.selectbox("Duration", ('Today', '7 Day', '1 Month', 'Custom'))
    
    selected_event_names = st.multiselect('Select Event Name', event_names, default=default_events)

     # Mapping of titles to their respective pids
    pid_mapping = {
     #   "Tax Planning for Salaried Individuals": "207e1ddb-70d7-4adf-9a8c-17c4a79d7547",
        "Basics of Fundamental Analysis": "37a3bf71-9f89-44dc-af65-870ad64835aa",
        "Basics of Stock Market": "3f2973a2-b6f2-4c18-ba1d-4c48346937b6",
        "Basics of Options": "40a39a1b-bda0-4d54-82f8-2d453ad3187f",
        "Basics of Personal Finance": "a4c8f1f0-da64-48d2-8432-dd42d79e67c6",
        "Basics of Technical Analysis": "f4747acb-e1f7-458a-94bb-1a154d256795"
    }

    # User interface to select a programme by title
    #selected_title = st.selectbox('Select Programme Title', list(pid_mapping.keys()))     //added later

    # Retrieve the pid from the selected title
    #selected_pid = pid_mapping[selected_title]   //added later

    # User interface to select multiple programmes by title
    selected_titles = st.multiselect('Select Programme Titles', list(pid_mapping.keys()))
    
    # Retrieve the pids from the selected titles
    selected_pids = [pid_mapping[title] for title in selected_titles]
    
        # Create two columns for the date inputs
    col1, col2 = st.columns(2)
    
    # Date input for fromDate in the first column
    with col1:
        fromDate = st.date_input("From Date", date.today())
    
    # Date input for toDate in the second column
    with col2:
        toDate = st.date_input("To Date", date.today())

# Submit button to trigger the data fetching
if st.button('Fetch Data'):
    # Dynamic URLs and event names for the APIs based on selected event names and date range
    tasks = [
        (f"https://oracle.varsitylive.in/admin/web-analytics/click/{event_name}/{pid}/range?fromDate={fromDate}&toDate={toDate}", event_name)
        for pid in selected_pids for event_name in selected_event_names
       # for event_name in selected_event_names   //added later
    ]

    # Fetch and display data concurrently for the selected event names and date range
    with ThreadPoolExecutor() as executor:
        data_frames = list(executor.map(lambda x: fetch_clicks(*x), tasks))

    # Combine all data into a single DataFrame
    if data_frames:
        combined_data = pd.concat(data_frames, ignore_index=True)
        combined_data['date'] = pd.to_datetime(combined_data['date']).dt.date

        # Display the data in a single table with event names as column headers
        pivot_table = combined_data.pivot_table(index='date', columns='event_name', values='clicks', aggfunc='sum').fillna(0)
       # st.table(pivot_table)

        # Plotting all events in a single chart
        plt.figure(figsize=(10, 6))
        for event_name in pivot_table.columns:
            plt.plot(pivot_table.index, pivot_table[event_name], marker='o', linestyle='-', label=event_name)

        # Formatting the plot
        plt.title('Clicks over Time by Event')
        plt.xlabel('Date')
        plt.ylabel('Number of Clicks')
        plt.xticks(rotation=45)
        plt.legend(title='Event Names')
        plt.grid(True)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))

        # Display the plot in the Streamlit app
        st.pyplot(plt)
