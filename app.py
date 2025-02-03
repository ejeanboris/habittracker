import streamlit as st
import pandas as pd
import datetime
import uuid
import json
import os
from io import BytesIO
from ics import Calendar, Event
import plotly.graph_objects as go
import requests

DATA_FILE = "config/habits.csv"
ICS_FILE_PATH = "config/habit_calendar.ics"

# Nextcloud Configuration
NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL")
NEXTCLOUD_USERNAME = os.getenv("NEXTCLOUD_USERNAME")
NEXTCLOUD_PASSWORD = os.getenv("NEXTCLOUD_PASSWORD")

# Load habit data
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df["logs"] = df["logs"].apply(lambda x: json.loads(x) if isinstance(x, str) else {})
        return df
    else:
        return pd.DataFrame(columns=["id", "name", "repeat", "start_date", "end_date", "type", "logs"])

data = load_data()

# Save data and update ICS
def save_data():
    df = data.copy()
    df["logs"] = df["logs"].apply(json.dumps)  # Convert logs to string before saving
    df.to_csv(DATA_FILE, index=False)
    update_and_save_ics()  # Call ICS update function

# Function to upload ICS file to Nextcloud via WebDAV
def upload_to_nextcloud():
    """Uploads the ICS file to Nextcloud."""
    with open(ICS_FILE_PATH, "rb") as file:
        response = requests.put(
            NEXTCLOUD_URL + "habit_calendar.ics",  # Remote path in Nextcloud
            data=file,
            auth=(NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD),
        )

    if response.status_code in [200, 201, 204]:
        pass #print("✅ ICS file uploaded successfully to Nextcloud!")
    else:
        st.error(f"❌ Failed to upload ICS file: {response.status_code} - {response.text}")



# Function to generate and save the ICS calendar
def update_and_save_ics():
    """Generate and save the ICS calendar."""
    if not data.empty:
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
                event.make_all_day()  # This ensures it's treated as an all-day event
                # Add completion percentage as event description
                completion = logs.get(str(date.date()), 0)
                event.description = f"Completion: {completion}%"
                
                cal.events.add(event)

        # Save the ICS file
        with open(ICS_FILE_PATH, "w") as ics_file:
            ics_file.writelines(cal)
    else:
        # Remove ICS file if no habits exist
        if os.path.exists(ICS_FILE_PATH):
            os.remove(ICS_FILE_PATH)
    
    # Call to upload to nextcloud
    upload_to_nextcloud()

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
            
            if new_completion != completion:  # Only update if value changed
                logs[str(today)] = new_completion
                data.at[idx, "logs"] = json.dumps(logs)
                save_data()
    else:
        st.write("No scheduled habits for today.")

# Sidebar for managing habits
st.sidebar.subheader("Manage Habits")

if not data.empty:
    habit_names = data["name"].tolist()
    habit_selection = st.sidebar.selectbox("Select a habit to edit/remove", habit_names)

    if habit_selection:
        habit_idx = data[data["name"] == habit_selection].index[0]
        habit_row = data.iloc[habit_idx]

        # Edit habit form
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

        # Remove habit button
        if st.sidebar.button("Remove Habit"):
            data = data.drop(index=habit_idx).reset_index(drop=True)
            save_data()
            st.sidebar.success("Habit removed successfully!")
            st.rerun()

else:
    st.sidebar.write("No habits available. Add a new habit below.")

# Sidebar section to add a new habit
st.sidebar.subheader("Add a New Habit")
new_habit_name = st.sidebar.text_input("Habit Name")
new_habit_repeat = st.sidebar.selectbox("Repeatability", ["Daily", "Weekly", "Monthly", "Yearly"])
new_habit_start = st.sidebar.date_input("Start Date", datetime.date.today())
new_habit_end = st.sidebar.date_input("End Date", datetime.date.today())
new_habit_type = st.sidebar.selectbox("Habit Type", ["Done/Not Done", "Progress"])

if st.sidebar.button("Add Habit"):
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

# Provide a direct link to the ICS file
st.subheader("Download or Access Your ICS Calendar")
if os.path.exists(ICS_FILE_PATH):
    with open(ICS_FILE_PATH, "rb") as f:
        st.download_button(
            label="Download ICS Calendar",
            data=f,
            file_name="habit_calendar.ics",
            mime="text/calendar",
        )
    st.markdown("[Access ICS Calendar Directly](./getcalendar)")# Link to the new download page
else:
    st.warning("No habits found to generate a calendar.")


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










import numpy as np

# 📆 Generate GitHub-style calendar heatmap using Plotly
st.subheader("Habit Completion Heatmap")
habit_selection = st.selectbox("Select a habit to visualize:", ["All Habits"] + list(data["name"].unique()))

# Prepare data for the heatmap
habit_logs = []
for _, row in data.iterrows():
    habit_name = row["name"]
    logs = row["logs"]
    if isinstance(logs, str):
        logs = json.loads(logs)  # Ensure logs are converted to a dictionary
    for date, completion in logs.items():
        habit_logs.append({"Habit": habit_name, "Date": date, "Completion": completion})

# Convert to DataFrame
df_completed = pd.DataFrame(habit_logs)
df_completed["Date"] = pd.to_datetime(df_completed["Date"])

# Apply filtering
if habit_selection != "All Habits":
    df_completed = df_completed[df_completed["Habit"] == habit_selection]

# Ensure at least one entry exists
if df_completed.empty:
    st.warning("No habit data available. Displaying a blank heatmap.")
    df_completed = pd.DataFrame(columns=["DayOfWeek", "Week", "Completion", "Date"])

# Extract necessary time fields
df_completed["Week"] = df_completed["Date"].dt.isocalendar().week
df_completed["DayOfWeek"] = df_completed["Date"].dt.dayofweek  # 0=Monday, 6=Sunday
df_completed["DayNumber"] = df_completed["Date"].dt.day  # Get the actual numeric day of the month

# 🔹 FIX: Ensure all 7 days (0-6) and weeks (1-52) are present
all_weeks = list(range(1, 53))  # Full year (52 weeks)
all_days = list(range(0, 7))  # Full week (Monday to Sunday)

# Generate a full calendar grid
full_grid = []
for week in all_weeks:
    for day in all_days:
        try:
            guessed_date = pd.Timestamp.strptime(f"2024 {week} {day}", "%Y %W %w").date()
            full_grid.append({"DayOfWeek": day, "Week": week, "Completion": 0, "DayNumber": guessed_date.day})
        except:
            full_grid.append({"DayOfWeek": day, "Week": week, "Completion": 0, "DayNumber": np.nan})  # Keep NaN for invalid dates

# Convert full grid to DataFrame
full_grid_df = pd.DataFrame(full_grid)

# 🔹 Merge with actual habit data (Fill missing values with 0%)
df_completed = df_completed.groupby(["DayOfWeek", "Week"], as_index=False).agg({"Completion": "sum", "DayNumber": "first"})
df_filled = full_grid_df.merge(df_completed, on=["DayOfWeek", "Week"], how="left")
df_filled["Completion"] = df_filled["Completion_y"].fillna(0)
df_filled["DayNumber"] = df_filled["DayNumber_x"].fillna(" ")  # Ensure every box has a visible day number
df_filled = df_filled[["DayOfWeek", "Week", "Completion", "DayNumber"]]

# 🔹 Pivot table for heatmap
heatmap_data = df_filled.pivot(index="DayOfWeek", columns="Week", values="Completion")
day_numbers = df_filled.pivot(index="DayOfWeek", columns="Week", values="DayNumber")

# Ensure valid x and y values
weeks = heatmap_data.columns.tolist()
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]  # Full 7-day week

# 🔹 Ensure `z_values` is a 2D array
z_values = heatmap_data.values
if z_values.ndim == 1:
    z_values = np.expand_dims(z_values, axis=0)  # Convert to 2D

# **Ensure day numbers are displayed correctly and avoid `ValueError`**
day_texts = np.array([[str(day_numbers.iloc[i, j]) if pd.notna(day_numbers.iloc[i, j]) and str(day_numbers.iloc[i, j]).strip() != "" else " "
                        for j in range(day_numbers.shape[1])] for i in range(day_numbers.shape[0])])

# **🔹 Adjust figure size to ensure SQUARE CELLS**
cell_size = 50  # Increase cell size to ensure readability
fig_width = cell_size * len(weeks)  # Scale width based on number of weeks
fig_height = cell_size * len(days)  # Scale height based on 7 days

# Prepare Plotly heatmap
fig = go.Figure(data=go.Heatmap(
    z=z_values,
    x=weeks,  # Weeks on the x-axis
    y=list(range(0, 7)),  # Ensure all 7 days are plotted
    colorscale="blues",  # ✅ Valid colorscale
    showscale=False,  # Always show color scale
    hoverinfo="x+y+z",
    xgap=5,  # 🔹 Increase spacing to avoid overlap
    ygap=5,  # 🔹 Increase spacing to avoid overlap
    text=day_texts,  # **Overlay day numbers**
    texttemplate="%{text}",  # **Ensure text is visible**
    textfont={"size": 16, "color": "green", "family": "Arial Black"},  # **Make text GREEN and larger**
))

# Transparent background
fig.update_layout(
    title=f"{habit_selection} Completion Heatmap",
    title_font_color="white",
    xaxis=dict(
        title="Week Number",
        tickmode="array",
        tickvals=weeks,
        ticktext=[str(week) for week in weeks],
        showgrid=False,
        zeroline=False,
        tickfont=dict(color="white"),
    ),
    yaxis=dict(
        title="Day of Week",
        tickmode="array",
        tickvals=[0, 3, 6],  # Only show labels for Mon, Thu, Sun
        ticktext=["Mon", "Thu", "Sun"],
        showgrid=False,
        zeroline=False,
        tickfont=dict(color="white"),
    ),
    autosize=False,
    height=fig_height,  # 🔹 Dynamically set height to keep squares
    width=fig_width,  # 🔹 Dynamically set width to keep squares
    plot_bgcolor="rgba(0,0,0,0)",  # Transparent background
    paper_bgcolor="rgba(0,0,0,0)",  # Transparent background
)

# Highlight the current week
current_week = datetime.date.today().isocalendar().week
if current_week in weeks:
    fig.add_shape(
        type="rect",
        xref="x", yref="paper",
        x0=current_week - 0.5, x1=current_week + 0.5,
        y0=0, y1=1,
        line=dict(color="red", width=2),
    )

# 🔹 Ensure the chart is actually rendered
st.write("Plotly Heatmap Ready")

# Display in Streamlit
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})





# **🔹 Section to log past habit completion**
st.subheader("Log Habit Completion for Any Date")

# **🔹 Date selector (allows logging for past dates)**
selected_date = st.date_input("Select Date", datetime.date.today())

# **🔹 Show habits scheduled for the selected date**
if not data.empty:
    selected_habits = data[
        (pd.to_datetime(data["start_date"]).dt.date <= selected_date) & 
        (pd.to_datetime(data["end_date"]).dt.date >= selected_date)
    ]

    if not selected_habits.empty:
        for idx, row in selected_habits.iterrows():
            habit_id = row["id"]
            logs = row["logs"]
            
            if isinstance(logs, str):  # Ensure logs are treated as a dictionary
                logs = json.loads(logs)

            # **Retrieve previously logged completion or default to 0%**
            completion = logs.get(str(selected_date), 0)

            # **Slider to log habit completion percentage**
            new_completion = st.slider(f"{row['name']} completion % ({selected_date})", 0, 100, int(completion), key=f"{habit_id}_{selected_date}")

            # **Only update if value changed**
            if new_completion != completion:
                logs[str(selected_date)] = new_completion
                data.at[idx, "logs"] = json.dumps(logs)
                save_data()
                st.success(f"✅ Logged {new_completion}% completion for '{row['name']}' on {selected_date}")
    else:
        st.write("No scheduled habits for the selected date.")
else:
    st.write("No habits available.")