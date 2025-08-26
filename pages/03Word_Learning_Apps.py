import math
import os
import random
import re
import tempfile

import pandas as pd
import streamlit as st
from gtts import gTTS

# ---------------- Page setup ----------------
st.set_page_config(page_title="Word Practice")
st.markdown("### 🐥 단어 학습 어플리케이션 (Word learning App)")

# ---------------- Data ----------------
CSV_URL = "https://raw.githubusercontent.com/jihyeon0531/WordApp/refs/heads/main/data/2025_Ch6_8_0819.csv"
df = pd.read_csv(CSV_URL)

# Safety: ensure required columns exist (now includes 'Set')
required_cols = {"Word", "Meaning", "Sentence", "Translation", "Set"}
missing = required_cols - set(df.columns)
if missing:
    st.error(f"CSV is missing columns: {', '.join(missing)}")
    st.stop()

# --- Build sets by 'Set' column (e.g., set1 ~ set6) ---
# Normalize/ensure order: sort by the numeric part if present
def _set_sort_key(val):
    m = re.search(r"\d+", str(val))
    return int(m.group()) if m else float("inf")

# Keep only relevant columns (optional, for cleanliness)
df = df[["Set", "Word", "Meaning", "Sentence", "Translation"]].copy()

# Group by Set and order groups set1..set6
grouped = sorted(df.groupby("Set"), key=lambda kv: _set_sort_key(kv[0]))
sets = [g.reset_index(drop=True) for _, g in grouped]  # list of DataFrames in order

# Labels for the dropdown (show all 10 words in each option)
set_labels = []
for set_name, g in grouped:
    words = ", ".join(g["Word"].astype(str).tolist())
    set_labels.append(f"{set_name}: {words}")

# ---------------- Session state ----------------
if "selected_words" not in st.session_state:
    st.session_state.selected_words = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "selected_set_idx" not in st.session_state:
    st.session_state.selected_set_idx = 0  # default to first set

# Quiz state
if "quiz_qid" not in st.session_state:
    st.session_state.quiz_qid = 0
if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "answer_shown" not in st.session_state:
    st.session_state.answer_shown = False

# ---------------- be verb handling ------------------------------
import re

def make_highlight_pattern(phrase: str) -> re.Pattern:
    """
    Build a regex that matches the phrase in the sentence,
    handling common inflections if it starts with 'be '.
    """
    ph = phrase.strip()
    # Special-case leading 'be ' → any be-form
    if ph.lower().startswith("be "):
        rest = re.escape(ph[3:].strip())            # 'good at' -> 'good\ at'
        be_forms = r"(?:am|is|are|was|were|be|being|been)"
        pattern = rf"\b{be_forms}\s+{rest}\b"
    else:
        # Default: exact phrase match with word boundaries
        pattern = rf"\b{re.escape(ph)}\b"
    return re.compile(pattern, flags=re.IGNORECASE)

def highlight_phrase(sentence: str, phrase: str, color="orange") -> str:
    pat = make_highlight_pattern(phrase)
    return pat.sub(lambda m: f"<span style='color:{color}; font-weight:bold'>{m.group(0)}</span>",
                   sentence)

# ---------------- Helper: make a new quiz question ----------------
def make_quiz_question():
    chunk = sets[st.session_state.selected_set_idx]
    # Pick a random row from this set
    row = chunk.sample(1, random_state=random.randrange(0, 10_000)).iloc[0]
    ans_word = str(row["Word"])
    sentence = str(row["Sentence"])
    translation = str(row["Translation"])

    # Cloze the answer word once (underline blank)
    pattern = r"\b" + re.escape(ans_word) + r"\b"
    cloze_sentence = re.sub(
        pattern, "<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>", sentence, count=1, flags=re.IGNORECASE
    )

    # Build options: 1 correct + 3 distractors from the same set, then "None of the above"
    words_pool = [str(w) for w in chunk["Word"].tolist()]
    distractors = [w for w in words_pool if w.lower() != ans_word.lower()]
    random.shuffle(distractors)
    distractors = distractors[:3] if len(distractors) >= 3 else distractors

    options = distractors + [ans_word]
    random.shuffle(options)
    options.append("None of the above")  # always last

    st.session_state.quiz = {
        "word": ans_word,
        "sentence": sentence,
        "sentence_cloze": cloze_sentence,
        "translation": translation,
        "options": options,
    }
    st.session_state.quiz_qid += 1
    st.session_state.answer_shown = False

# ---------------- Tabs ----------------
tab1, tab2 = st.tabs(["1️⃣ Select Words", "2️⃣ Learning"])

# ---------------- Tab 1: Select ----------------
with tab1:
    st.markdown("### ✨ Step 1: Choose a set, then pick words to practice")

    # Dropdown to select a set
    current_index = (
        st.session_state.selected_set_idx
        if st.session_state.selected_set_idx < len(set_labels)
        else 0
    )
    chosen_label = st.selectbox(
        "📚 Select a 10-word set",
        set_labels,
        index=current_index,
        key="word_set_select",
    )

    # Detect changed set and reset selections when the set changes
    new_index = set_labels.index(chosen_label)
    if new_index != st.session_state.selected_set_idx:
        st.session_state.selected_set_idx = new_index
        st.session_state.selected_words = []
        st.session_state.submitted = False
        st.session_state.quiz = None  # reset quiz when set changes

    # The slice for this set
    practice_df = sets[st.session_state.selected_set_idx]

    st.caption("아래에서 연습할 단어를 체크하세요. **Tab 2**에서 뜻/예문/음성을 제공합니다.")

    # Use a form to group the checkboxes & submit
    with st.form("word_select_form"):
        selected = []
        for i, row in practice_df.iterrows():
            cb_key = f"set{st.session_state.selected_set_idx}_word_{i}"
            checked = st.checkbox(f"{row['Word']} ({row['Meaning']})", key=cb_key)
            if checked:
                selected.append(row["Word"])
        submitted = st.form_submit_button("✨ 선택완료 버튼!")

    if submitted:
        st.session_state.selected_words = selected
        st.session_state.submitted = True

    # Feedback
    if st.session_state.submitted:
        count = len(st.session_state.selected_words)
        if count > 0:
            st.success(f"🎉 You selected {count} word(s) for practice:")
            st.write(", ".join(st.session_state.selected_words))
        else:
            st.warning("⚠️ You did not select any words.")

# ---------------- Tab 2: Practice ----------------
with tab2:
    st.markdown("### ✨ Step 2: Then, let's practice the words that you chose.")
    if not st.session_state.submitted or len(st.session_state.selected_words) == 0:
        st.info("Please go to **Tab 1** and select words first.")
    else:
        st.write(f"연습할 단어는 {len(st.session_state.selected_words)} 개입니다:")

        for idx, word in enumerate(st.session_state.selected_words, start=1):
            # Find the row for this word within the selected set (fallback to full df)
            current_chunk = sets[st.session_state.selected_set_idx]
            row = current_chunk[current_chunk["Word"] == word]
            if row.empty:
                row = df[df["Word"] == word]
            row = row.iloc[0]

            sentence = str(row["Sentence"])
            meaning = str(row["Meaning"])
            translation = str(row["Translation"])

            highlighted_sentence = highlight_phrase(sentence, word)

            st.markdown(f"### {idx}. {word}")
            st.markdown(
                f"<span style='color:gray'><b>뜻:</b> {meaning}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"예문: <i>{highlighted_sentence}</i> "
                f"<span style='color:gray'>({translation})</span>",
                unsafe_allow_html=True,
            )

            # Generate and play audio using gTTS
            try:
                tts = gTTS(sentence)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                    tts.save(fp.name)
                    st.audio(fp.name, format="audio/mp3")
            except Exception as e:
                st.warning(f"Audio unavailable for this sentence. ({e})")

            st.write("---")
