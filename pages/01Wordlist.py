import streamlit as st
import pandas as pd

# Set up page
st.set_page_config(page_title="Test App")
st.title("Hello, Students!")

# Load the CSV from GitHub
CSV_URL = "https://raw.githubusercontent.com/jihyeon0531/WordApp/refs/heads/main/data/wdata01.csv"
df = pd.read_csv(CSV_URL)

# Create tabs
tab1, tab2 = st.tabs(["Intro", "Word list"])

# Tab 1: Intro
with tab1:
    st.write("Welcome to the app.")
    st.markdown("""
        This app helps you practice vocabulary.
        
        👉 Go to the **Word list** tab to review words.  
        👉 Later, you can try quizzes and practice exercises!
    """)

# Tab 2: Word List
with tab2:
    st.header("📋 Vocabulary Word List")
    st.dataframe(df, use_container_width=True)
