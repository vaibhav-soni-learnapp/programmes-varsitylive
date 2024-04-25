import streamlit as st
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Streamlit application title
st.title('API Clicks Fetcher')

# Authorization token
auth_token = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiIxODUyZmZmNi02N2RlLTRiNjYtYmIwMy01NDJlY2Q4YmZmNzMiLCJhZG0iOnRydWUsImlhdCI6MTcxNDAyMzA5NiwiZXhwIjoxNzE0MTA5NDk2LCJhdWQiOiJwbGF0bzowLjAuMSIsImlzcyI6InZhcnNpdHktbGl2ZSJ9.N2b4Gymi_LC79320WNE1-1b9pVPt5Qty-rScVEsgRQA'
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
    selected_event_names = st.multiselect('Select Event Name', event_names, default=default_events)

    # Date input for fromDate and toDate
    fromDate = st.date_input("From Date", date.today())
    toDate = st.date_input("To Date", date.today())

    # Dynamic URLs and event names for the APIs based on selected event names and date range
    tasks = [
        (f"https://oracle.varsitylive.in/admin/web-analytics/click/{event_name}/3f2973a2-b6f2-4c18-ba1d-4c48346937b6/range?fromDate={fromDate}&toDate={toDate}", event_name)
        for event_name in selected_event_names
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
        st.table(pivot_table)

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
