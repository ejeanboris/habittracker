import streamlit as st
import pandas as pd
import datetime

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
        df.loc[df.index[df["Date"] == today][index], "Completed"] = checked
        save_data(df)
        st.rerun()

# Show habit history
st.subheader("Habit History")
st.dataframe(df.sort_values(by=["Date", "Habit"], ascending=[False, True]))
