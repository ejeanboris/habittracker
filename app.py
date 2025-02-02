import streamlit as st
import pandas as pd
import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import random
import numpy as np

# Load or initialize habit data
def load_data():
    try:
        df = pd.read_csv("habits.csv")
        if "Completed" in df.columns:
            df["Completed"] = df["Completed"].astype(bool)
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "Habit", "Completed"])

def save_data(df):
    df.to_csv("habits.csv", index=False)

# Generate dummy data for testing (Optional)
def generate_dummy_data():
    habits = ["Exercise", "Read", "Meditate", "Code", "Drink Water"]
    dates = pd.date_range(start="2024-01-01", periods=365).strftime("%Y-%m-%d").tolist()
    data = []
    for date in dates:
        for habit in habits:
            data.append([date, habit, random.choice([True, False])])
    return pd.DataFrame(data, columns=["Date", "Habit", "Completed"])

# Optionally generate dummy data only if needed
if st.sidebar.checkbox("Generate Dummy Data for Testing"):
    df = load_data()
    dummy_data = generate_dummy_data()
    df = pd.concat([df, dummy_data], ignore_index=True).drop_duplicates()
    save_data(df)

# Streamlit UI
st.title("Habit Tracker")

today = str(datetime.date.today())
current_week = datetime.date.today().isocalendar()[1]

# Load existing data
df = load_data()

df_today = df[df["Date"] == today]

# Check off daily habits section at the top
st.subheader("Check Off Today's Habits")
for index, row in df_today.iterrows():
    checked = st.checkbox(row["Habit"], value=row["Completed"], key=f"habit_{index}")
    if checked != row["Completed"]:
        df.at[index, "Completed"] = checked
        save_data(df)
        st.rerun()

st.subheader("Track Today's Habits")
habit = st.text_input("Add a new habit:")
if st.button("Add Habit"):
    if habit and habit not in df_today["Habit"].values:
        new_entry = pd.DataFrame([[today, habit, False]], columns=["Date", "Habit", "Completed"])
        df = pd.concat([df, new_entry], ignore_index=True)
        save_data(df)
        st.rerun()

# Log habit completion
st.subheader("Log Habit Completion")
habit_to_log = st.selectbox("Select a habit to log:", df["Habit"].unique())
date_to_log = st.date_input("Select a date:", datetime.date.today())
if st.button("Log Habit"):
    date_str = str(date_to_log)
    if not df[(df["Date"] == date_str) & (df["Habit"] == habit_to_log)].empty:
        df.loc[(df["Date"] == date_str) & (df["Habit"] == habit_to_log), "Completed"] = True
        save_data(df)
        st.rerun()
    else:
        st.warning("This habit is not listed for the selected date. Please add it first.")

# Show habit history
st.subheader("Habit History")
st.dataframe(df.sort_values(by=["Date", "Habit"], ascending=[False, True]))

# Generate GitHub-style calendar heatmap
st.subheader("Habit Completion Heatmap")
habit_selection = st.selectbox("Select a habit to visualize:", ["All Habits"] + list(df["Habit"].unique()))

if habit_selection == "All Habits":
    df_completed = df[df["Completed"] == True].copy()
else:
    df_completed = df[(df["Completed"] == True) & (df["Habit"] == habit_selection)].copy()

if not df_completed.empty:
    df_completed["Date"] = pd.to_datetime(df_completed["Date"])
    df_completed["Count"] = 1
    df_completed["Week"] = df_completed["Date"].dt.isocalendar().week
    df_completed["DayOfWeek"] = df_completed["Date"].dt.dayofweek
    df_completed["Month"] = df_completed["Date"].dt.strftime('%b')
    heatmap_data = df_completed.groupby(["DayOfWeek", "Week"]).agg({"Count": "sum"}).reset_index()
    heatmap_data = heatmap_data.pivot(index="DayOfWeek", columns="Week", values="Count").fillna(0)
    
    fig, ax = plt.subplots(figsize=(16, 8))
    heatmap = sns.heatmap(heatmap_data, cmap="crest", cbar=False, linewidths=2, linecolor='gray', ax=ax, square=True)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    ax.set_title(f"{habit_selection} Completion Heatmap", color="white")
    ax.set_xlabel("Week Number", color="white")
    ax.set_ylabel("Day of Week", color="white")
    ax.set_yticks([0, 3, 6])
    ax.set_yticklabels(["Mon", "Thu", "Sun"], rotation=0, color="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.tick_params(axis='both', colors='white')
    
    # Highlight current week
    if current_week in heatmap_data.columns:
        ax.add_patch(plt.Rectangle((heatmap_data.columns.get_loc(current_week), 0), 1, len(heatmap_data), fill=False, edgecolor='red', lw=2))
    
    # Add week numbers on top
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    ax.set_xticks(heatmap_data.columns)
    ax.set_xticklabels(heatmap_data.columns, color="white", fontsize=10)
    
    # Add month labels only at the start of the month, positioned directly below the heatmap
    unique_months = df_completed.groupby("Week").first().reset_index()
    month_starts = unique_months.groupby("Month")["Week"].first().reset_index()
    month_ticks = month_starts["Week"].values
    month_labels = month_starts["Month"].values
    ax_secondary = ax.secondary_xaxis(-0.1)
    ax_secondary.set_xticks(month_ticks)
    ax_secondary.set_xticklabels(month_labels, color="white", fontsize=12)
    ax_secondary.spines['bottom'].set_visible(False)
    ax_secondary.xaxis.set_tick_params(length=0)
    
    st.pyplot(fig)
