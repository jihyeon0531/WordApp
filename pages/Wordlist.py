import streamlit as st
import pandas as pd
import random

# Load the CSV from GitHub
CSV_URL = "https://raw.githubusercontent.com/jihyeon0531/WordApp/refs/heads/main/data/wdata01.csv"
df = pd.read_csv(CSV_URL)

# Initialize session state for selected row
if "selected_row" not in st.session_state:
    st.session_state.selected_row = None

# Page title
st.set_page_config(page_title="Vocabulary Practice App", layout="wide")
st.title("📘 Vocabulary Practice App")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Introduction", "Wordlist", "Practice"])

# --------- Tab 1: Introduction ---------
with tab1:
    st.header("🧾 How to Use This App")
    st.markdown("""
    Welcome to the Vocabulary Practice App!  
    Here's how to use it:
    
    1. **Wordlist** tab shows all vocabulary items.
       - Click on any word to highlight it and view its details.
    2. **Practice** tab presents a random sentence with one word missing.
       - Try to guess the missing word and get instant feedback.
    """)

# --------- Tab 2: Wordlist (Interactive) ---------
with tab2:
    st.header("📋 Wordlist")

    # Let user select a row by Word
    selected_word = st.radio("Click a word to highlight:", df["Word"].tolist(), horizontal=True)

    # Find selected row index
    selected_index = df[df["Word"] == selected_word].index[0]
    st.session_state.selected_row = selected_index

    # Highlight selected row
    def highlight_row(s):
        return ['background-color: lightyellow' if i == st.session_state.selected_row else '' for i in range(len(s))]

    # Display styled dataframe
    st.dataframe(df, use_container_width=True)



# --------- Tab 3: Practice (Single Word Fill-in-the-Blank) ---------
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
