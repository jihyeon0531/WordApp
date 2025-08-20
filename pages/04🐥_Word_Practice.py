# practice_mcq_app.py
import random
import re
from typing import List, Dict

import pandas as pd
import streamlit as st

# -------------------------------------------------
# Config
# -------------------------------------------------
st.set_page_config(page_title="Word Practice (MCQ)")

CSV_URL = "https://raw.githubusercontent.com/jihyeon0531/WordApp/refs/heads/main/data/wdata01.csv"
# Expected columns in CSV: Word, Meaning, Sentence, Translation
# Optionally, a Set column (e.g., Set = 1,2,3...), otherwise we chunk every 10 rows as one set.

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    # basic hygiene
    needed = ["Word", "Meaning", "Sentence", "Translation"]
    for col in needed:
        if col not in df.columns:
            raise ValueError(f"CSV is missing required column: {col}")
    return df

def build_sets(df: pd.DataFrame, size: int = 10) -> Dict[str, pd.DataFrame]:
    """
    Return a dict mapping set name -> 10-row slice (or grouped by 'Set' if present).
    """
    # If a 'Set' column exists, group by it; otherwise chunk by 10.
    set_col = None
    for candidate in ["Set", "set", "SetID", "Set_Id", "SetName"]:
        if candidate in df.columns:
            set_col = candidate
            break

    sets = {}
    if set_col:
        for sid, g in df.groupby(set_col):
            g = g.reset_index(drop=True)
            sets[f"Set {sid}"] = g
    else:
        total = len(df)
        set_idx = 1
        for start in range(0, total, size):
            end = min(start + size, total)
            slice_df = df.iloc[start:end].reset_index(drop=True)
            if len(slice_df) > 0:
                sets[f"Set {set_idx}"] = slice_df
                set_idx += 1
    return sets

AUX_MAP = {
    "be":   r"(?:am|is|are|was|were|be|being|been)",
    "have": r"(?:have|has|had|having)",
    "do":   r"(?:do|does|did|doing)",
}

def make_match_pattern(phrase: str) -> re.Pattern:
    """Build a regex that matches the phrase in the sentence, handling be/have/do variants."""
    ph = phrase.strip()
    parts = ph.split()
    if parts and parts[0].lower() in AUX_MAP and len(parts) > 1:
        rest = re.escape(" ".join(parts[1:]))
        head = AUX_MAP[parts[0].lower()]
        pattern = rf"\b{head}\s+{rest}\b"
    else:
        pattern = rf"\b{re.escape(ph)}\b"
    return re.compile(pattern, flags=re.IGNORECASE)

def mask_phrase(sentence: str, phrase: str) -> str:
    """
    Replace the matched phrase with an underlined blank.
    If not found, return the original sentence.
    """
    pat = make_match_pattern(phrase)
    blank = "<span style='border-bottom:2px solid #222;'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>"
    return pat.sub(blank, sentence, count=1)

def make_mcq_options(correct: str, pool: List[str], k_distractors: int = 3) -> List[str]:
    """
    Build 4 options from the set (1 correct + 3 distractors), plus 'None of the above' as the last option.
    """
    distractors = [w for w in pool if w != correct]
    random.shuffle(distractors)
    distractors = distractors[:k_distractors]
    opts = distractors + [correct]
    random.shuffle(opts)  # randomize position of correct among first 4
    opts.append("None of the above")  # always last
    return opts

def reset_question():
    st.session_state.current_q = None
    st.session_state.user_choice = None
    st.session_state.answered = False

# -------------------------------------------------
# Load data and prepare sets
# -------------------------------------------------
df = load_data(CSV_URL)
sets = build_sets(df, size=10)
set_names = list(sets.keys())

# -------------------------------------------------
# App Title
# -------------------------------------------------
st.markdown("### 🐥 단어 연습 앱 (Word Practice App)")

# -------------------------------------------------
# Tabs
# -------------------------------------------------
tab1, tab2, tab3 = st.tabs(["1️⃣ Practice 1: 문장속 단어", "2️⃣ Practice 2", "3️⃣ Practice 3"])

# -------------------------------------------------
# Tab 1: Practice 1 (MCQ app from your old Tab 3)
# -------------------------------------------------
with tab1:
    st.markdown("#### 세트 선택")
    if "selected_set" not in st.session_state:
        st.session_state.selected_set = set_names[0] if set_names else None
    if "current_q" not in st.session_state:
        st.session_state.current_q = None
    if "user_choice" not in st.session_state:
        st.session_state.user_choice = None
    if "answered" not in st.session_state:
        st.session_state.answered = False

    set_choice = st.selectbox("연습할 단어 세트를 선택하세요:", set_names, index=set_names.index(st.session_state.selected_set) if st.session_state.selected_set in set_names else 0)
    if set_choice != st.session_state.selected_set:
        st.session_state.selected_set = set_choice
        reset_question()

    cur_df = sets[st.session_state.selected_set].copy()

    st.divider()
    st.markdown("#### 연습 시작")

    colA, colB = st.columns([1,1])
    with colA:
        if st.button("🟢 새 문제 시작 (Start)"):
            # Pick a random target row from this set
            row = cur_df.sample(1, random_state=random.randint(0, 10_000)).iloc[0]
            target_word = str(row["Word"])
            sentence = str(row["Sentence"])
            translation = str(row["Translation"])

            # Build masked sentence (underline blank where phrase appears)
            masked = mask_phrase(sentence, target_word)

            # Build options (4 from set including correct + 'None of the above' as last)
            pool_words = [str(w) for w in cur_df["Word"].tolist()]
            options = make_mcq_options(target_word, pool_words, k_distractors=3)

            # Save current question
            st.session_state.current_q = {
                "word": target_word,
                "sentence": sentence,
                "masked": masked,
                "translation": translation,
                "options": options
            }
            st.session_state.user_choice = None
            st.session_state.answered = False

    with colB:
        if st.button("🔁 초기화 (Reset)"):
            reset_question()

    st.write("")  # spacing

    if st.session_state.current_q is None:
        st.info("‘새 문제 시작’ 버튼을 눌러 연습을 시작하세요.")
    else:
        q = st.session_state.current_q


        # The question prompt
        st.markdown("**Q:** 다음 문장의 의미로 보아 밑줄 친 부분에 들어갈 가장 적절한 단어는?")
        # Show sentence (masked) and translation
        st.markdown(
            f"<div style='font-size:16px; line-height:1.6'><b>문장:</b> {q['masked']}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='color:gray;'>( {q['translation']} )</div>",
            unsafe_allow_html=True
        )


        # Options (radio)
        st.session_state.user_choice = st.radio(
            "정답을 선택하세요:",
            q["options"],
            index=None,
            key="mcq_choice",
        )

        # Answer button
        if st.button("정답 확인 (Show me the answer)"):
            if st.session_state.user_choice is None:
                st.warning("먼저 보기를 선택하세요.")
            else:
                st.session_state.answered = True
                if st.session_state.user_choice == q["word"]:
                    st.success("Correct ✅")
                    st.balloons()
                else:
                    st.error(f"Incorrect ❌  |  정답: {q['word']}")

        # Optional: reveal full sentence with highlight after answering
        if st.session_state.answered:
            # Highlight the actual phrase in the original sentence
            def highlight_phrase(sentence: str, phrase: str, color="orange") -> str:
                pat = make_match_pattern(phrase)
                return pat.sub(lambda m: f"<span style='color:{color}; font-weight:bold'>{m.group(0)}</span>", sentence)

            highlighted = highlight_phrase(q["sentence"], q["word"])
            st.markdown("**원문 표시:**", unsafe_allow_html=True)
            st.markdown(
                f"<div style='font-size:16px; line-height:1.6'>{highlighted}</div>",
                unsafe_allow_html=True
            )

# -------------------------------------------------
# Tab 2 & 3: placeholders
# -------------------------------------------------
with tab2:
    st.markdown("### Practice 2")
    st.info("이 탭은 추후에 연습 2 기능을 추가할 예정입니다.")

with tab3:
    st.markdown("### Practice 3")
    st.info("이 탭은 추후에 연습 3 기능을 추가할 예정입니다.")
