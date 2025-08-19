import streamlit as st
import pandas as pd
from gtts import gTTS
import tempfile
import os

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
st.markdown("### 📝 Word Practice App: 1st Set")

# Tabs
tab1, tab2, tab3 = st.tabs(["1️⃣ Select Words", "2️⃣ Practice", "3️⃣ Summary"])

# ---------------- Tab 1 ----------------
with tab1:

    st.write("단어 학습 어플리케이션 (Word learning App)")
    st.markdown("### ✨ Step 1: Choose words to practice")
    st.markdown("""
        🐣 안녕~! 내가 학습할 어휘를 도와줄게 :-)
        목록에 나온 단어들 중에서 내가 잘 모르겠다 생각되는 단어를 선택하면 됩니다. 그러면 선택한 단어들의 뜻, 발음, 그리고 어떻게 문장에 사용하는지를 학습할 수 있어요.
    """)
    # Use a form to group checkboxes and submission
    with st.form("word_select_form"):
        selected = []
        for i, row in practice_df.iterrows():
            checked = st.checkbox(f"{row['Word']} ({row['Meaning']})", key=f"word_{i}")
            if checked:
                selected.append(row["Word"])

        submitted = st.form_submit_button("✨ Click to start!")
        st.caption("선택된 단어들을 가지고 두 번째 탭에서 연습하게 됩니다.")

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

from gtts import gTTS
import tempfile

# ---------------- Tab 2 ----------------
with tab2:
    st.markdown("### 🐧 Step 2: 자, 이제 선택한 단어들을 학습해 봅시다.")
    if not st.session_state.submitted or len(st.session_state.selected_words) == 0:
        st.info("Please go to **Tab 1** and select words first.")
    else:
        st.write(f"연습할 단어는 {len(st.session_state.selected_words)} 개입니다:")

        for idx, word in enumerate(st.session_state.selected_words, start=1):
            row = df[df["Word"] == word].iloc[0]
            sentence = row['Sentence']
            meaning = row['Meaning']
            translation = row['Translation']

            # Highlight the word in the sentence (case-sensitive)
            highlighted_sentence = sentence.replace(
                word, f"<span style='color:orange; font-weight:bold'>{word}</span>"
            )

            # Display word, meaning, example, translation, and audio
            st.markdown(f"### {idx}. {word}")
            st.markdown(f"<span style='color:gray'><b>뜻:</b> {meaning}</span>", unsafe_allow_html=True)
            st.markdown(
                f"예문: <i>{highlighted_sentence}</i> <span style='color:gray'>({translation})</span>",
                unsafe_allow_html=True
            )


            # Generate and play audio using gTTS
            tts = gTTS(sentence)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tts.save(fp.name)
                st.audio(fp.name, format="audio/mp3")

            st.write("---")


# ---------------- Tab 3 ----------------
with tab3:
    st.header("📊 Step 3: Summary (Coming Soon)")
    st.write("You can show quiz scores, notes, or export options here later.")
