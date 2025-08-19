import streamlit as st
import pandas as pd
import random

# Load CSV data from GitHub
CSV_URL = "https://raw.githubusercontent.com/jihyeon0531/WordApp/refs/heads/main/data/wdata01.csv"
df = pd.read_csv(CSV_URL)

# Set page config
st.set_page_config(page_title="Vocabulary Practice App", layout="wide")
st.title("📘 Vocabulary Practice App")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Introduction", "Wordlist", "Practice"])

# -------- Tab 1: Introduction --------
with tab1:
    st.header("🧾 How to Use This App")
    st.markdown("""
    Welcome to the Vocabulary Practice App!  
    Here's how to use it:

    1. **Wordlist** tab: Browse the vocabulary list and review meanings.
    2. **Practice** tab: Try filling in the blanks using the vocabulary in context.
    """)

# -------- Tab 2: Wordlist --------
with tab2:
    st.header("📋 Wordlist Table")
    st.dataframe(df, use_container_width=True)

# -------- Tab 3: Practice --------
with tab3:
    st.header("📝 Vocabulary Practice")

    row = df.sample(n=1).iloc[0]
    sentence_with_blank = row["Sentence"].replace(row["Word"], "_____")

    st.markdown("### Fill in the blank:")
    st.write(sentence_with_blank)

    user_input = st.text_input("Type the missing word:")

    if user_input:
        if user_input.strip().lower() == row["Word"].lower():
            st.success("✅ Correct!")
        else:
            st.error(f"❌ Incorrect. The correct word is **{row['Word']}**.")

        with st.expander("🔍 See meaning and translation"):
            st.markdown(f"- **Meaning**: {row['Meaning']}")
            st.markdown(f"- **Korean Translation**: {row['Translation']}")
