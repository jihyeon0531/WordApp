import streamlit as st
import pandas as pd

# Set up page
st.set_page_config(page_title="Test App")
st.markdown("### 🍰 맛있는 단어장")

# Load the CSV from GitHub
CSV_URL = "https://raw.githubusercontent.com/jihyeon0531/WordApp/refs/heads/main/data/2025_Ch6_8_0819.csv"
df = pd.read_csv(CSV_URL)

# Display without index
st.dataframe(df, hide_index=True)


# Create tabs
tab1, tab2 = st.tabs(["🐾 1. 설명페이지", "🐋 2. Word list"])

# Tab 1: Intro
with tab1:
    st.write("단어 학습 어플리케이션 (Word learning App)")
    st.markdown("""
        🐣 위쪽 두 번째 탭을 클릭하면 모두 99개의 단어가 뜻, 문장에서의 예시 등이 함께 있습니다 :-)

        연습을 시작하려면 왼쪽 메뉴에서 10개씩 준비된 세트(Set)을 선택하시면 됩니다.

    """)

# Tab 2: Word List
with tab2:
    st.markdown("### 📋 Word list (전체 단어 목록)")
    st.dataframe(df, use_container_width=True)
