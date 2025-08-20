import streamlit as st
import pandas as pd

# Set up page
st.set_page_config(page_title="Test App")
st.markdown("### 🍰 맛있는 단어장")

# Load the CSV from GitHub
CSV_URL = "https://raw.githubusercontent.com/jihyeon0531/WordApp/refs/heads/main/data/2025_Ch6_8_0819.csv"
df = pd.read_csv(CSV_URL)


# Create tabs
tab1, tab2 = st.tabs(["🐾 1. 설명페이지", "🐋 2. Word list"])

# Tab 1: Intro
with tab1:
    st.write("단어 학습 어플리케이션 (Word learning App)")
    st.markdown("""
        🐣 위쪽 두 번째 탭에는 총 87개 단어가 뜻, 문장 예시, 문장 해석 등이 함께 있습니다 :-)

        시작하려면 왼쪽 메뉴에서 학습앱(Learning APP) 또는 연습앱(Practice APP)을 클릭하세요.

    """)

# Tab 2: Word List
with tab2:
    st.markdown("### 📋 Word list (전체 단어 목록)")
    # Display without index
    st.dataframe(df, hide_index=True)

    PDF_URL = "https://github.com/jihyeon0531/WordApp/raw/main/data/wordlist-0821.pdf"
    st.markdown(f"[💾 Download]({PDF_URL}) Word list PDF file: 6 pages", unsafe_allow_html=True)

