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

# Generate dummy data for testing
def generate_dummy_data():
    habits = ["Exercise", "Read", "Meditate", "Code", "Drink Water"]
    dates = pd.date_range(start="2024-01-01", periods=365).strftime("%Y-%m-%d").tolist()
    data = []
    for date in dates:
        for habit in habits:
            data.append([date, habit, random.choice([True, False])])
    return pd.DataFrame(data, columns=["Date", "Habit", "Completed"])

df = generate_dummy_data()
save_data(df)

# Streamlit UI
st.title("Habit Tracker")

today = str(datetime.date.today())

# Load existing data
df = load_data()

df_today = df[df["Date"] == today]

st.subheader("Track Today's Habits")
habit = st.text_input("Add a new habit:")
if st.button("Add Habit"):
    if habit and habit not in df_today["Habit"].values:
        new_entry = pd.DataFrame([[today, habit, False]], columns=["Date", "Habit", "Completed"])
        df = pd.concat([df, new_entry], ignore_index=True)
        save_data(df)
        st.rerun()

# Display habits for today
for index, row in df_today.iterrows():
    checked = st.checkbox(row["Habit"], value=row["Completed"], key=f"habit_{index}")
    if checked != row["Completed"]:
        df.at[index, "Completed"] = checked
        save_data(df)
        st.rerun()

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
    heatmap_data = df_completed.groupby(["DayOfWeek", "Week"]).agg({"Count": "sum"}).reset_index()
    heatmap_data = heatmap_data.pivot(index="DayOfWeek", columns="Week", values="Count").fillna(0)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.heatmap(heatmap_data, cmap="Greens", cbar=False, linewidths=1, linecolor='gray', ax=ax, square=True)
    fig.patch.set_alpha(0)
    ax.set_facecolor("none")
    ax.set_title(f"{habit_selection} Completion Heatmap")
    ax.set_xlabel("Week Number")
    ax.set_ylabel("Day of Week")
    ax.set_yticks(range(7))
    ax.set_yticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], rotation=0)
    st.pyplot(fig)
