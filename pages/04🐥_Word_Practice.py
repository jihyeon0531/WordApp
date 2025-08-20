# practice_mcq_app.py
import random
import re
import io
from typing import List, Dict

import pandas as pd
import streamlit as st
from gtts import gTTS

# -------------------------------------------------
# Config
# -------------------------------------------------
st.set_page_config(page_title="Word Practice")

CSV_URL = "https://raw.githubusercontent.com/jihyeon0531/WordApp/refs/heads/main/data/wdata01.csv"
# Expected columns in CSV: Word, Meaning, Sentence, Translation
# Optionally, a Set column (e.g., Set = 1,2,3...), otherwise chunk by 10 rows as one set.

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    needed = ["Word", "Meaning", "Sentence", "Translation"]
    for col in needed:
        if col not in df.columns:
            raise ValueError(f"CSV is missing required column: {col}")
    return df

def build_sets(df: pd.DataFrame, size: int = 10) -> Dict[str, pd.DataFrame]:
    """Return dict: set name -> 10-row slice (or grouped by 'Set' if present)."""
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
    """Regex that matches the phrase in the sentence, handling be/have/do variants."""
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
    """Replace the matched phrase with an underlined blank once."""
    pat = make_match_pattern(phrase)
    blank = "<span style='border-bottom:2px solid #222;'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>"
    return pat.sub(blank, sentence, count=1)

def make_mcq_options(correct: str, pool: List[str], k_distractors: int = 3) -> List[str]:
    """4 options (1 correct + 3 distractors) + 'None of the above' as last option."""
    distractors = [w for w in pool if w != correct]
    random.shuffle(distractors)
    distractors = distractors[:k_distractors]
    opts = distractors + [correct]
    random.shuffle(opts)
    opts.append("None of the above")
    return opts

def reset_q1():
    st.session_state.current_q1 = None
    st.session_state.user_choice_q1 = None
    st.session_state.answered_q1 = False

def reset_q2():
    st.session_state.current_q2 = None
    st.session_state.user_spelling = ""
    st.session_state.answered_q2 = False
    st.session_state.audio_bytes_q2 = None

def tts_mp3(word: str, lang: str = "en") -> bytes:
    """Generate TTS MP3 bytes for the given word/phrase."""
    tts = gTTS(text=word, lang=lang)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()

def normalize_answer(s: str) -> str:
    """Lowercase and remove spaces/punctuation for robust matching."""
    return re.sub(r"[^a-z0-9]+", "", s.lower())

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
tab1, tab2, tab3 = st.tabs(["1️⃣ Practice 1: 문장 속 단어", "2️⃣ Practice 2: 듣고 써보기", "3️⃣ Practice 3"])

# -------------------------------------------------
# Tab 1: 문장 속 단어 (MCQ)
# -------------------------------------------------
with tab1:
    st.markdown("#### 1. 세트 선택")
    if "selected_set" not in st.session_state:
        st.session_state.selected_set = set_names[0] if set_names else None
    if "current_q1" not in st.session_state:
        st.session_state.current_q1 = None
    if "user_choice_q1" not in st.session_state:
        st.session_state.user_choice_q1 = None
    if "answered_q1" not in st.session_state:
        st.session_state.answered_q1 = False

    set_choice = st.selectbox(
        "Choose a word set to practice:",
        set_names,
        index=set_names.index(st.session_state.selected_set) if st.session_state.selected_set in set_names else 0,
        key="set_select_q1",
    )
    if set_choice != st.session_state.selected_set:
        st.session_state.selected_set = set_choice
        reset_q1()
        reset_q2()  # keep both tabs in sync when set changes

    cur_df = sets[st.session_state.selected_set].copy()

    st.markdown("#### 2. 연습 시작")
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("🍅 새 문제 시작 (Start)", key="start_q1"):
            row = cur_df.sample(1, random_state=random.randint(0, 10_000)).iloc[0]
            target_word = str(row["Word"])
            sentence = str(row["Sentence"])
            translation = str(row["Translation"])
            masked = mask_phrase(sentence, target_word)
            pool_words = [str(w) for w in cur_df["Word"].tolist()]
            options = make_mcq_options(target_word, pool_words, k_distractors=3)
            st.session_state.current_q1 = {
                "word": target_word,
                "sentence": sentence,
                "masked": masked,
                "translation": translation,
                "options": options
            }
            st.session_state.user_choice_q1 = None
            st.session_state.answered_q1 = False

    with colB:
        if st.button("🔁 초기화 (Reset)", key="reset_q1"):
            reset_q1()

    if st.session_state.current_q1 is None:
        st.info("‘새 문제 시작’ 버튼을 눌러 연습을 시작하세요.")
    else:
        q = st.session_state.current_q1
        st.divider()
        st.markdown("**Q:** 다음 문장의 의미로 보아 밑줄 친 부분에 들어갈 가장 적절한 단어는?")
        st.markdown(
            f"<div style='font-size:16px; line-height:1.6'><b>문장:</b> {q['masked']}</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div style='color:gray;'>( {q['translation']} )</div>",
            unsafe_allow_html=True
        )
        st.write("")
        st.session_state.user_choice_q1 = st.radio(
            "정답을 선택하세요:",
            q["options"],
            index=None,
            key="mcq_choice_q1",
        )

        if st.button("정답 확인 (Show me the answer)", key="check_q1"):
            if st.session_state.user_choice_q1 is None:
                st.warning("먼저 보기를 선택하세요.")
            else:
                st.session_state.answered_q1 = True
                if st.session_state.user_choice_q1 == q["word"]:
                    st.success("Correct ✅")
                    st.balloons()
                else:
                    st.error(f"Incorrect ❌  |  정답: {q['word']}")

        if st.session_state.answered_q1:
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
# Tab 2: 듣고 스펠링 입력 (대소문자/공백/문장부호 무시)
# -------------------------------------------------
with tab2:
    st.markdown("#### 1. 세트 선택 (탭1과 동일)")
    if "current_q2" not in st.session_state:
        st.session_state.current_q2 = None
    if "user_spelling" not in st.session_state:
        st.session_state.user_spelling = ""
    if "answered_q2" not in st.session_state:
        st.session_state.answered_q2 = False
    if "audio_bytes_q2" not in st.session_state:
        st.session_state.audio_bytes_q2 = None

    set_choice2 = st.selectbox(
        "Choose a word set to practice:",
        set_names,
        index=set_names.index(st.session_state.selected_set) if st.session_state.selected_set in set_names else 0,
        key="set_select_q2",
    )
    if set_choice2 != st.session_state.selected_set:
        st.session_state.selected_set = set_choice2
        reset_q1()
        reset_q2()

    cur_df2 = sets[st.session_state.selected_set].copy()

    st.markdown("#### 2. 연습 시작")
    colC, colD = st.columns([1, 1])
    with colC:
        if st.button("🔊 새 문제 시작 (Start & Listen)", key="start_q2"):
            row = cur_df2.sample(1, random_state=random.randint(0, 10_000)).iloc[0]
            target_word = str(row["Word"])
            # generate audio for the word/phrase
            audio_bytes = tts_mp3(target_word, lang="en")
            st.session_state.current_q2 = {
                "word": target_word
            }
            st.session_state.audio_bytes_q2 = audio_bytes
            st.session_state.user_spelling = ""
            st.session_state.answered_q2 = False

    with colD:
        if st.button("🔁 초기화 (Reset)", key="reset_q2"):
            reset_q2()

    if st.session_state.current_q2 is None:
        st.info("‘새 문제 시작’ 버튼을 눌러 단어를 듣고 스펠링을 입력하세요.")
    else:
        q2 = st.session_state.current_q2

        # Audio player (replayable)
        if st.session_state.audio_bytes_q2:
            st.audio(st.session_state.audio_bytes_q2, format="audio/mp3")
        else:
            st.warning("오디오를 불러오는 중 문제가 발생했습니다. 다시 시작해 주세요.")

        # Input spelling
        st.write("")
        st.markdown("**Q:** 들은 단어(또는 어구)의 스펠링을 입력하세요.")
        st.session_state.user_spelling = st.text_input(
            "정답 입력:",
            value=st.session_state.user_spelling,
            key="spelling_input",
            placeholder="예: be good at",
        )

        # Check answer (ignore case, spaces, punctuation)
        if st.button("정답 확인 (Check spelling)", key="check_q2"):
            user_norm = normalize_answer(st.session_state.user_spelling)
            correct_norm = normalize_answer(q2["word"])

            st.session_state.answered_q2 = True
            if user_norm and user_norm == correct_norm:
                st.success("Correct ✅")
                st.balloons()
            else:
                st.error(f"Incorrect ❌  |  정답: {q2['word']}")

# -------------------------------------------------
# Tab 3: Placeholder (추후 확장)
# -------------------------------------------------
with tab3:
    st.markdown("### Practice 3")
    st.info("이 탭은 추후에 연습 3 기능을 추가할 예정입니다.")
