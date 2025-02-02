import streamlit as st
import os
from io import BytesIO

ICS_FILE_PATH = "habit_calendar.ics"

st.title("Downloading Your ICS File...")

# Check if the ICS file exists
if os.path.exists(ICS_FILE_PATH):
    with open(ICS_FILE_PATH, "rb") as f:
        ics_bytes = BytesIO(f.read())  # Load the file into memory
    
    # Auto-download by showing the download button immediately
    st.download_button(
        label="Click here if the download does not start automatically",
        data=ics_bytes,
        file_name="habit_calendar.ics",
        mime="text/calendar",
    )

    # Auto-trigger download using JavaScript
    st.markdown(
        f"""
        <script>
            var downloadLink = document.createElement('a');
            downloadLink.href = 'data:text/calendar;charset=utf-8,' + encodeURIComponent({ics_bytes.getvalue().decode()});
            downloadLink.download = 'habit_calendar.ics';
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
        </script>
        """,
        unsafe_allow_html=True,
    )

else:
    st.warning("ICS file not found. Please generate the file first.")
