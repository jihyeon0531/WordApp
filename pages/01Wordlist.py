import streamlit as st
import pandas as pd

# Set up page
st.set_page_config(page_title="Test App")
st.markdown("### 🍰 맛있는 단어장")

# Load the CSV from GitHub
CSV_URL = "https://raw.githubusercontent.com/jihyeon0531/WordApp/refs/heads/main/data/wdata01.csv"
df = pd.read_csv(CSV_URL)

# Create tabs
tab1, tab2 = st.tabs(["🐾 1. 설명페이지", "🐋 2. Word list"])

# Tab 1: Intro
with tab1:
    st.write("단어 학습 어플리케이션 (Word learning App)")
    st.markdown("""
        제가 학습할 어휘를 도와줄게요.
        <설명>
        👉 먼저 위쪽에 있는 🐋**2. Word list** tab을 클릭하면 단어 목록을 볼 수 있어요.  
        👉 잘 모르겠다 생각되는 단어를 선택하시면 그 단어들을 연습하도록 도와줄 거예요!
    """)

# Tab 2: Word List
with tab2:
    st.markdown("### 📋 Word list (전체 단어 목록)")
    st.dataframe(df, use_container_width=True)
