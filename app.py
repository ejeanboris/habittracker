import streamlit as st
import pandas as pd
import datetime
import uuid
import ics
import os
from ics import Calendar, Event
from io import BytesIO
import plotly.graph_objects as go

DATA_FILE = "habits.csv"

# Load habit data
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["id", "name", "repeat", "start_date", "end_date", "type", "logs"])

data = load_data()

# Save data function
def save_data():
    data.to_csv(DATA_FILE, index=False)

# UI title
st.title("Habit Tracker")

# Section to add a new habit
st.subheader("Add a New Habit")
name = st.text_input("Habit Name")
repeat = st.selectbox("Repeatability", ["Daily", "Weekly", "Monthly", "Yearly"])
start_date = st.date_input("Start Date", datetime.date.today())
end_date = st.date_input("End Date", datetime.date.today())
habit_type = st.selectbox("Habit Type", ["Done/Not Done", "Progress"])

if st.button("Add Habit"):
    new_habit = {
        "id": str(uuid.uuid4()),
        "name": name,
        "repeat": repeat,
        "start_date": start_date,
        "end_date": end_date,
        "type": habit_type,
        "logs": "{}",
    }
    data = pd.concat([data, pd.DataFrame([new_habit])], ignore_index=True)
    save_data()
    st.success("Habit added successfully!")
    st.rerun()

# Sidebar for managing habits
st.sidebar.subheader("Manage Habits")
if not data.empty:
    habit_selection = st.sidebar.selectbox("Select a habit to edit/remove", data["name"] if not data.empty else ["No habits available"])
    
    if habit_selection and habit_selection in data["name"].values:
        habit_id = data[data["name"] == habit_selection]["id"].values[0]
        
        if st.sidebar.button("Remove Habit"):
            data = data[data["id"] != habit_id]
            save_data()
            st.sidebar.success("Habit removed successfully!")
            st.rerun()
        
        st.sidebar.subheader("Edit Habit")
        new_name = st.sidebar.text_input("Edit Habit Name", habit_selection)
        habit_row = data[data["id"] == habit_id]
        if not habit_row.empty:
            new_repeat = st.sidebar.selectbox("Edit Repeatability", ["Daily", "Weekly", "Monthly", "Yearly"], index=["Daily", "Weekly", "Monthly", "Yearly"].index(habit_row["repeat"].values[0]))
            new_start_date = st.sidebar.date_input("Edit Start Date", habit_row["start_date"].values[0])
            new_end_date = st.sidebar.date_input("Edit End Date", habit_row["end_date"].values[0])
            new_type = st.sidebar.selectbox("Edit Habit Type", ["Done/Not Done", "Progress"], index=["Done/Not Done", "Progress"].index(habit_row["type"].values[0]))
            
            if st.sidebar.button("Update Habit"):
                data.loc[data["id"] == habit_id, ["name", "repeat", "start_date", "end_date", "type"]] = [new_name, new_repeat, new_start_date, new_end_date, new_type]
                save_data()
                st.sidebar.success("Habit updated successfully!")

# Log habits section
st.subheader("Log Habit Completion")
if not data.empty:
    log_habit = st.selectbox("Select Habit to Log", data["name"])
    log_date = st.date_input("Date of Completion", datetime.date.today())
    
    if st.button("Log Habit"):
        habit_id = data[data["name"] == log_habit]["id"].values[0]
        data.loc[data["id"] == habit_id, "logs"].values[0] = "Completed"
        save_data()
        st.success("Habit logged successfully!")

# Display habits in a real calendar
st.subheader("Scheduled Habits Calendar")
if not data.empty:
    events = []
    for _, row in data.iterrows():
        habit_name = row["name"]
        start_date = row["start_date"]
        end_date = row["end_date"]
        repeat = row["repeat"]
        
        date_range = pd.date_range(start=start_date, end=end_date, freq={'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M', 'Yearly': 'Y'}[repeat])
        for date in date_range:
            events.append((date, habit_name))
    
    calendar_df = pd.DataFrame(events, columns=["Date", "Habit"])
    fig = go.Figure()
    for habit in calendar_df["Habit"].unique():
        habit_events = calendar_df[calendar_df["Habit"] == habit]
        fig.add_trace(go.Scatter(x=habit_events["Date"], y=[habit]*len(habit_events), mode='markers', name=habit))
    
    fig.update_layout(title="Habit Calendar", xaxis_title="Date", yaxis_title="Habits", showlegend=True)
    st.plotly_chart(fig)

# Generate and share ICS Calendar
st.subheader("Download Calendar")
if not data.empty:
    cal = Calendar()
    for _, row in data.iterrows():
        habit_name = row["name"]
        start_date = row["start_date"]
        end_date = row["end_date"]
        repeat = row["repeat"]
        
        date_range = pd.date_range(start=start_date, end=end_date, freq={'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M', 'Yearly': 'Y'}[repeat])
        for date in date_range:
            event = Event()
            event.name = habit_name
            event.begin = date.strftime("%Y-%m-%d")
            cal.events.add(event)
    
    ics_file = BytesIO()
    ics_file.write(str(cal).encode("utf-8"))
    ics_file.seek(0)
    st.download_button(label="Download ICS Calendar", data=ics_file, file_name="habits.ics", mime="text/calendar")
