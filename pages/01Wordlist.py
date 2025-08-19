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
    st.write("단어 학습 어플리케이션입니다.")
    st.markdown("""
        학습할 어휘를 도와줄게요.
        
        👉 먼저 **Word list** tab을 클릭하면 단어 목록을 볼 수 있어요.  
        👉 다른 활동은 곧 추가될 거예요!
    """)

# Tab 2: Word List
with tab2:
    st.header("📋 Set 1")
    st.dataframe(df, use_container_width=True)
