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
CSV_URL = "https://raw.githubusercontent.com/jihyeon0531/WordApp/refs/heads/main/data/wdata01.csv"
df = pd.read_csv(CSV_URL)

# Safety: ensure required columns exist
required_cols = {"Word", "Meaning", "Sentence", "Translation"}
missing = required_cols - set(df.columns)
if missing:
    st.error(f"CSV is missing columns: {', '.join(missing)}")
    st.stop()

# Chunk the dataframe into sets of 10 words
def chunk_df(frame, size=10):
    return [frame.iloc[i:i + size].reset_index(drop=True) for i in range(0, len(frame), size)]

sets = chunk_df(df, size=10)

# Labels for the dropdown (show all 10 words in each option)
set_labels = []
for i, chunk in enumerate(sets, start=1):
    words = ", ".join(chunk["Word"].astype(str).tolist())
    set_labels.append(f"Set {i}: {words}")

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

# ---------------- Helper: make a new quiz question ----------------
def make_quiz_question():
    chunk = sets[st.session_state.selected_set_idx]
    # Pick a random row from this 10-word set
    row = chunk.sample(1, random_state=random.randrange(0, 10_000)).iloc[0]
    ans_word = str(row["Word"])
    sentence = str(row["Sentence"])
    translation = str(row["Translation"])

    # Cloze the answer word once (underline blank)
    pattern = r"\b" + re.escape(ans_word) + r"\b"
    cloze_sentence = re.sub(
        pattern, "<u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u>", sentence, count=1, flags=re.IGNORECASE
    )

    # Build options: 1 correct + 3 distractors from the same set, then "None of the above" at the end
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
tab1, tab2, tab3 = st.tabs(["1️⃣ Select Words", "2️⃣ Learning", "3️⃣ Practice"])

# ---------------- Tab 1: Select ----------------
with tab1:
    st.markdown("### ✨ Step 1: Choose a set, then pick words to practice")

    # Dropdown to select a 10-word set
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

    # The 10-word slice for this set
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
    st.markdown("### 🐧 Step 2: 자, 이제 선택한 단어들을 학습해 봅시다.")
    if not st.session_state.submitted or len(st.session_state.selected_words) == 0:
        st.info("Please go to **Tab 1** and select words first.")
    else:
        st.write(f"연습할 단어는 {len(st.session_state.selected_words)} 개입니다:")

        for idx, word in enumerate(st.session_state.selected_words, start=1):
            # Find the row for this word (search only within the selected set for robustness)
            current_chunk = sets[st.session_state.selected_set_idx]
            row = current_chunk[current_chunk["Word"] == word]
            if row.empty:
                # Fallback: search the whole df if not found in the chunk
                row = df[df["Word"] == word]
            row = row.iloc[0]

            sentence = str(row["Sentence"])
            meaning = str(row["Meaning"])
            translation = str(row["Translation"])

            # Highlight the word in the sentence (simple case-sensitive replace)
            highlighted_sentence = sentence.replace(
                word, f"<span style='color:orange; font-weight:bold'>{word}</span>"
            )

            # Display word, meaning, example, translation, and audio
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

# ---------------- Tab 3: Quiz (from the 10-word set) ----------------
with tab3:
    st.header("🧠 Step 3: Set 기반 퀴즈")
    st.write("현재 선택된 10개 단어 세트에서 무작위로 문제를 출제합니다.")

    # Start/Next button
    if st.button("🎯 문제 시작 / 다음 문제"):
        make_quiz_question()

    # If we have a quiz question, render it
    if st.session_state.quiz:
        q = st.session_state.quiz

        # Show sentence (font size 16) with cloze underline
        st.markdown(
            f"<div style='font-size:16px;'>{q['sentence_cloze']}</div>",
            unsafe_allow_html=True,
        )
        # Show translation in gray, in parentheses
        st.markdown(
            f"<div style='color:gray;'>( {q['translation']} )</div>",
            unsafe_allow_html=True,
        )

        st.markdown("**질문:** 다음 문장의 의미로 보아 밑줄 친 부분에 들어갈 가장 적절한 단어는?")

        # Options (last one is always "None of the above")
        choice = st.radio(
            "정답 선택",
            q["options"],
            key=f"quiz_choice_{st.session_state.quiz_qid}",
            label_visibility="collapsed",
        )

        # Answer button
        if st.button("✅ 정답 보기", key=f"show_answer_{st.session_state.quiz_qid}"):
            st.session_state.answer_shown = True
            correct = (choice == q["word"])
            if correct:
                st.success("정답입니다! 🎉")
            else:
                st.error(f"아쉽습니다. 정답은 **{q['word']}** 입니다.")

    else:
        st.info("상단의 **문제 시작 / 다음 문제** 버튼을 눌러 퀴즈를 시작하세요.")
