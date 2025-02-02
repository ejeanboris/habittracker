import streamlit as st
import pandas as pd
import datetime
import uuid
import json
import os
from io import BytesIO
import plotly.graph_objects as go
from ics import Calendar, Event

DATA_FILE = "habits.csv"

# Load habit data
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Ensure logs column is converted to dictionaries
        df["logs"] = df["logs"].apply(lambda x: json.loads(x) if isinstance(x, str) else {})
        return df
    else:
        return pd.DataFrame(columns=["id", "name", "repeat", "start_date", "end_date", "type", "logs"])

data = load_data()

# Save data function
def save_data():
    df = data.copy()
    df["logs"] = df["logs"].apply(json.dumps)  # Convert logs to string before saving
    df.to_csv(DATA_FILE, index=False)

# UI title
st.title("Habit Tracker")

# Section to log today's habits
st.subheader("Log Today's Habit Completion")
if not data.empty:
    today = datetime.date.today()
    today_habits = data[
        (pd.to_datetime(data["start_date"]).dt.date <= today) & 
        (pd.to_datetime(data["end_date"]).dt.date >= today)
    ]
    
    if not today_habits.empty:
        for idx, row in today_habits.iterrows():
            habit_id = row["id"]
            logs = row["logs"]
            
            if isinstance(logs, str):  # Ensure logs are treated as a dictionary
                logs = json.loads(logs)

            completion = logs.get(str(today), 0)  # Default to 0% if not logged
            
            new_completion = st.slider(f"{row['name']} completion %", 0, 100, int(completion), key=habit_id)
            
            logs[str(today)] = new_completion  # Update completion percentage
            
            # Update logs in DataFrame
            data.at[idx, "logs"] = json.dumps(logs)  # Save back as JSON string
        
        save_data()
    else:
        st.write("No scheduled habits for today.")

# Generate ICS Calendar with Completion Logs
st.subheader("Download ICS Calendar")
if not data.empty:  # FIX: Corrected this line
    cal = Calendar()
    
    for _, row in data.iterrows():
        habit_name = row["name"]
        start_date = pd.to_datetime(row["start_date"]).date()
        end_date = pd.to_datetime(row["end_date"]).date()
        repeat = row["repeat"]
        logs = row["logs"]

        if isinstance(logs, str):  # Ensure logs are treated as a dictionary
            logs = json.loads(logs)
        
        date_range = pd.date_range(start=start_date, end=end_date, freq={'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M', 'Yearly': 'Y'}[repeat])
        
        for date in date_range:
            event = Event()
            event.name = habit_name
            event.begin = date.strftime("%Y-%m-%d")
            
            # Add completion percentage as a comment
            completion = logs.get(str(date.date()), 0)
            event.description = f"Completion: {completion}%"
            
            cal.events.add(event)
    
    ics_file = BytesIO()
    ics_file.write(str(cal).encode("utf-8"))
    ics_file.seek(0)
    st.download_button(label="Download ICS Calendar", data=ics_file, file_name="habits.ics", mime="text/calendar")

# Display habits in a calendar with completion status
st.subheader("Scheduled Habits Calendar")
if not data.empty:
    events = []
    for _, row in data.iterrows():
        habit_name = row["name"]
        start_date = pd.to_datetime(row["start_date"]).date()
        end_date = pd.to_datetime(row["end_date"]).date()
        repeat = row["repeat"]
        logs = row["logs"]

        if isinstance(logs, str):  # Ensure logs are treated as a dictionary
            logs = json.loads(logs)
        
        date_range = pd.date_range(start=start_date, end=end_date, freq={'Daily': 'D', 'Weekly': 'W', 'Monthly': 'M', 'Yearly': 'Y'}[repeat])
        
        for date in date_range:
            completion = logs.get(str(date.date()), 0)
            color = f"rgba(0, {completion * 2.55}, 0, 1)"  # Green scale based on completion percentage
            events.append((date, habit_name, color))
    
    calendar_df = pd.DataFrame(events, columns=["Date", "Habit", "Color"])
    fig = go.Figure()
    
    for habit in calendar_df["Habit"].unique():
        habit_events = calendar_df[calendar_df["Habit"] == habit]
        fig.add_trace(go.Scatter(x=habit_events["Date"], y=[habit]*len(habit_events), mode='markers', marker=dict(color=habit_events["Color"].tolist()), name=habit))
    
    fig.update_layout(title="Habit Calendar", xaxis_title="Date", yaxis_title="Habits", showlegend=True)
    st.plotly_chart(fig)

# Sidebar for managing habits
st.sidebar.subheader("Manage Habits")

if not data.empty:
    habit_names = data["name"].tolist()
    habit_selection = st.sidebar.selectbox("Select a habit to edit/remove", habit_names)

    if habit_selection:
        habit_idx = data[data["name"] == habit_selection].index[0]
        habit_row = data.iloc[habit_idx]

        # Pre-fill the form with existing habit data
        st.sidebar.subheader("Edit Habit")
        new_name = st.sidebar.text_input("Edit Habit Name", habit_row["name"])
        new_repeat = st.sidebar.selectbox(
            "Edit Repeatability", ["Daily", "Weekly", "Monthly", "Yearly"],
            index=["Daily", "Weekly", "Monthly", "Yearly"].index(habit_row["repeat"])
        )
        new_start_date = st.sidebar.date_input("Edit Start Date", pd.to_datetime(habit_row["start_date"]).date())
        new_end_date = st.sidebar.date_input("Edit End Date", pd.to_datetime(habit_row["end_date"]).date())
        new_type = st.sidebar.selectbox(
            "Edit Habit Type", ["Done/Not Done", "Progress"],
            index=["Done/Not Done", "Progress"].index(habit_row["type"])
        )

        if st.sidebar.button("Update Habit"):
            data.at[habit_idx, "name"] = new_name
            data.at[habit_idx, "repeat"] = new_repeat
            data.at[habit_idx, "start_date"] = str(new_start_date)
            data.at[habit_idx, "end_date"] = str(new_end_date)
            data.at[habit_idx, "type"] = new_type
            save_data()
            st.sidebar.success("Habit updated successfully!")
            st.rerun()

        # Button to remove habit
        if st.sidebar.button("Remove Habit", key=f"remove_{habit_idx}"):
            data = data.drop(index=habit_idx).reset_index(drop=True)
            save_data()
            st.sidebar.success("Habit removed successfully!")
            st.rerun()

else:
    st.sidebar.write("No habits available. Add a new habit below.")

# Sidebar section to add a new habit
st.sidebar.subheader("Add a New Habit")
new_habit_name = st.sidebar.text_input("Habit Name")
new_habit_repeat = st.sidebar.selectbox("Repeatability", ["Daily", "Weekly", "Monthly", "Yearly"], key="add_repeat")
new_habit_start = st.sidebar.date_input("Start Date", datetime.date.today(), key="add_start")
new_habit_end = st.sidebar.date_input("End Date", datetime.date.today(), key="add_end")
new_habit_type = st.sidebar.selectbox("Habit Type", ["Done/Not Done", "Progress"], key="add_type")

if st.sidebar.button("Add Habit", key="add_habit"):
    if new_habit_name:
        new_habit = {
            "id": str(uuid.uuid4()),
            "name": new_habit_name,
            "repeat": new_habit_repeat,
            "start_date": str(new_habit_start),
            "end_date": str(new_habit_end),
            "type": new_habit_type,
            "logs": json.dumps({}),  # Empty logs
        }
        data = pd.concat([data, pd.DataFrame([new_habit])], ignore_index=True)
        save_data()
        st.sidebar.success("Habit added successfully!")
        st.rerun()
    else:
        st.sidebar.warning("Please enter a habit name.")
