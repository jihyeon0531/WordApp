import streamlit as st
import pandas as pd

# Load the CSV
CSV_URL = "https://raw.githubusercontent.com/jihyeon0531/WordApp/refs/heads/main/data/wdata01.csv"
df = pd.read_csv(CSV_URL)

# Get first 10 words
practice_df = df.head(10)

# Initialize session state
if "selected_words" not in st.session_state:
    st.session_state.selected_words = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# Set page layout
st.set_page_config(page_title="Word Practice")
st.title("📝 Word Practice App")

# Tabs
tab1, tab2, tab3 = st.tabs(["1️⃣ Select Words", "2️⃣ Practice", "3️⃣ Summary"])

# ---------------- Tab 1 ----------------
with tab1:
    st.header("✅ Step 1: Choose words to practice")

    # Use a form to group checkboxes and submission
    with st.form("word_select_form"):
        selected = []
        for i, row in practice_df.iterrows():
            checked = st.checkbox(f"{row['Word']} ({row['Meaning']})", key=f"word_{i}")
            if checked:
                selected.append(row["Word"])

        submitted = st.form_submit_button("Submit Selection")

    # Save to session state if submitted
    if submitted:
        st.session_state.selected_words = selected
        st.session_state.submitted = True

    # Feedback to user
    if st.session_state.submitted:
        count = len(st.session_state.selected_words)
        if count > 0:
            st.success(f"🎉 You selected {count} word(s) for practice:")
            st.write(", ".join(st.session_state.selected_words))
        else:
            st.warning("⚠️ You did not select any words.")

# ---------------- Tab 2 ----------------
with tab2:
    st.header("🚀 Step 2: Practice Selected Words")
    if not st.session_state.submitted or len(st.session_state.selected_words) == 0:
        st.info("Please go to **Tab 1** and select words first.")
    else:
        st.write(f"You're practicing {len(st.session_state.selected_words)} word(s):")
        for word in st.session_state.selected_words:
            row = df[df["Word"] == word].iloc[0]
            st.markdown(f"**{row['Word']}** — {row['Meaning']}")
            st.write(f"Example: *{row['Sentence']}*")
            st.write("---")

# ---------------- Tab 3 ----------------
with tab3:
    st.header("📊 Step 3: Summary (Coming Soon)")
    st.write("You can show quiz scores, notes, or export options here later.")
