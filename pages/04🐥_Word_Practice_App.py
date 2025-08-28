# practice_mcq_app.py
import random
import re
import io
import os
from typing import List, Dict
from datetime import datetime
import base64
import pandas as pd
import streamlit as st
from gtts import gTTS

# -------------------------------------------------
# Config
# -------------------------------------------------
st.set_page_config(page_title="Word Practice")

# -------------------------------------------------
# Sidebar: version + controls
# -------------------------------------------------
#st.sidebar.caption(f"Build: practice_mcq_app.py | {datetime.now():%Y-%m-%d %H:%M:%S}")
#st.sidebar.caption(f"Streamlit {st.__version__}")
#st.sidebar.caption(f"Running file: {__file__}")
#st.sidebar.caption(f"WD: {os.getcwd()}")

# Force rerun (this session only)
#if st.sidebar.button("🔄 Force rerun", key="force_rerun_btn"):
#    st.rerun()

# Clear ONLY my session_state (safe for multi-user)
# if st.sidebar.button("🧹 Clear my session", key="wipe_state_btn"):
#     for k in list(st.session_state.keys()):
#         del st.session_state[k]
#     st.sidebar.success("Session state cleared.")
#     st.rerun()

# Clear app-wide data cache (affects ALL users)
# if st.sidebar.button("♻️ Refresh data (clear cache)", key="clear_cache_btn"):
#     st.cache_data.clear()
#     st.sidebar.success("Data cache cleared (global).")
#     st.rerun()

# -------------------------------------------------
# Data
# -------------------------------------------------
CSV_URL = "https://raw.githubusercontent.com/jihyeon0531/WordApp/refs/heads/main/data/2025_Ch6_8_0819.csv"
# Expected columns: Set, Word, Meaning, Sentence, Translation

# Cached CSV loader
@st.cache_data(ttl=300)
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    needed = ["Word", "Meaning", "Sentence", "Translation", "Set"]
    for col in needed:
        if col not in df.columns:
            raise ValueError(f"CSV is missing required column: {col}")
    return df[["Set", "Word", "Meaning", "Sentence", "Translation"]].copy()

def build_sets(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Group by 'Set' and return ordered mapping: set name -> DataFrame slice."""
    def _set_sort_key(val):
        m = re.search(r"\d+", str(val))
        return int(m.group()) if m else float("inf")

    groups = sorted(df.groupby("Set"), key=lambda kv: _set_sort_key(kv[0]))
    sets = {}
    for set_name, g in groups:
        sets[str(set_name)] = g.reset_index(drop=True)
    return sets

# -------------------------------------------------
# Text utilities
# -------------------------------------------------
AUX_MAP = {
    "be":   r"(?:am|is|are|was|were|be|being|been)",
    "have": r"(?:have|has|had|having)",
    "do":   r"(?:do|does|did|doing)",
}

def make_match_pattern(phrase: str) -> re.Pattern:
    """Regex that matches the phrase, handling be/have/do variants."""
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
    """Replace matched phrase with an underlined blank once."""
    pat = make_match_pattern(phrase)
    blank = "<span style='border-bottom:2px solid #222;'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>"
    return pat.sub(blank, sentence, count=1)

def make_mcq_options(correct: str, pool: List[str], k_distractors: int = 3) -> List[str]:
    """4 options (1 correct + 3 distractors) + 'None of the above' last."""
    distractors = [w for w in pool if w != correct]
    random.shuffle(distractors)
    distractors = distractors[:k_distractors]
    opts = distractors + [correct]
    random.shuffle(opts)
    opts.append("None of the above")
    return opts

def make_k_options_including_correct(correct: str, pool: List[str], k: int = 5) -> List[str]:
    """Build exactly k options including the correct answer (no 'None of the above')."""
    pool_unique = list(dict.fromkeys(pool))  # de-dup
    distractors = [w for w in pool_unique if w != correct]
    random.shuffle(distractors)
    need = max(0, k - 1)
    chosen = distractors[:need]
    opts = chosen + [correct]
    random.shuffle(opts)
    return opts[:k]

def normalize_answer(s: str) -> str:
    """Lowercase and remove spaces/punctuation for robust matching."""
    return re.sub(r"[^a-z0-9]+", "", s.lower())

# -------------------------------------------------
# Audio (gTTS) + cache
# -------------------------------------------------

def tts_mp3(word: str, lang: str = "en") -> bytes:
    """Generate TTS MP3 bytes for the given word/phrase."""
    tts = gTTS(text=word, lang=lang)
    buf = io.BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()

@st.cache_data(show_spinner=False, max_entries=1000)
def tts_cached(word: str, lang: str = "en") -> bytes:
    """Cached audio bytes per (word, lang)."""
    return tts_mp3(word, lang)

# ---------------- State resetters ----------------
def reset_all_for_set_change():
    reset_q1_all()
    reset_q2_all()
    reset_q3_all()

def reset_q1_all():
    st.session_state.current_q1 = None
    st.session_state.user_choice_q1 = None
    st.session_state.answered_q1 = False
    st.session_state.solved_q1 = set()
    st.session_state.remaining_q1 = []
    st.session_state.completed_q1 = False
    st.session_state.solved_current_q1 = False

def reset_q2_all():
    st.session_state.current_q2 = None
    st.session_state.user_spelling = ""
    st.session_state.answered_q2 = False
    st.session_state.audio_bytes_q2 = None
    st.session_state.solved_q2 = set()
    st.session_state.remaining_q2 = []
    st.session_state.completed_q2 = False
    st.session_state.solved_current_q2 = False

def reset_q3_all():
    st.session_state.current_q3 = None
    st.session_state.user_choice_q3 = None
    st.session_state.answered_q3 = False
    st.session_state.solved_q3 = set()
    st.session_state.remaining_q3 = []
    st.session_state.completed_q3 = False
    st.session_state.solved_current_q3 = False


#---------------------
# Audio play for iOS friendly version
#---------------------

def audio_html(audio_bytes, mime='audio/mp3'):
    b64 = base64.b64encode(audio_bytes).decode('utf-8')
    audio_tag = f"""
    <audio controls>
        <source src="data:{mime};base64,{b64}" type="{mime}">
        Your browser does not support the audio element.
    </audio>
    """
    return audio_tag

# -------------------------------------------------
# Load data and prepare sets
# -------------------------------------------------
df = load_data(CSV_URL)
sets = build_sets(df)
set_names = list(sets.keys())  # e.g., ['set1','set2',...,'set6']

if not set_names:
    st.error("No sets found. Please check the CSV.")
    st.stop()

# Helper for safe selectbox index
def _safe_index(names: List[str], selected: str | None) -> int:
    if selected in names:
        return names.index(selected)
    return 0

# -------------------------------------------------
# App Title
# -------------------------------------------------
st.markdown("### 🐥 단어 연습 앱 (Word Practice App)")

# -------------------------------------------------
# Tabs (order controls visual order)
# -------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "1️⃣ Practice 1: 단어-뜻 연습",
    "2️⃣ Practice 2: 문장 속 단어",
    "3️⃣ Practice 3: 스펠링연습"
])

# -------------------------------------------------
# Init shared and tab-specific state
# -------------------------------------------------
if "selected_set" not in st.session_state:
    st.session_state.selected_set = set_names[0]

# Tab1 state
for key, default in [
    ("current_q1", None),
    ("user_choice_q1", None),
    ("answered_q1", False),
    ("solved_q1", set()),
    ("remaining_q1", []),
    ("completed_q1", False),
    ("solved_current_q1", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Tab2 state
for key, default in [
    ("current_q2", None),
    ("user_spelling", ""),
    ("answered_q2", False),
    ("audio_bytes_q2", None),
    ("solved_q2", set()),
    ("remaining_q2", []),
    ("completed_q2", False),
    ("solved_current_q2", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# Tab3 state
for key, default in [
    ("current_q3", None),
    ("user_choice_q3", None),
    ("answered_q3", False),
    ("solved_q3", set()),
    ("remaining_q3", []),
    ("completed_q3", False),
    ("solved_current_q3", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# -------------------------------------------------
# Tab 1: 뜻 맞히기 (세트 내 5지선다, None 없음)
# -------------------------------------------------
with tab1:
    st.markdown("#### 1. 세트 선택")
    idx3 = _safe_index(set_names, st.session_state.selected_set)
    set_choice3 = st.selectbox(
        "Choose a word set to practice:",
        set_names,
        index=idx3,
        key="set_select_q3",
    )
    if set_choice3 != st.session_state.selected_set:
        st.session_state.selected_set = set_choice3
        cur_df3 = sets[st.session_state.selected_set].copy()
        st.session_state.remaining_q1 = list(cur_df3["Word"])
        st.session_state.remaining_q2 = list(cur_df3["Word"])
        st.session_state.remaining_q3 = list(cur_df3["Word"])
        reset_all_for_set_change()

    cur_df3 = sets[st.session_state.selected_set].copy()
    if not st.session_state.remaining_q3:
        st.session_state.remaining_q3 = list(cur_df3["Word"])

    st.markdown("#### 2. 연습 시작")
    colE, colF = st.columns([1, 1])

    with colE:
        if st.button("🍅 Start / Continue", key="start_q3"):
            if st.session_state.completed_q3:
                st.info("이 세트의 모든 문항을 완료했습니다. 🔒 ‘초기화’로 다시 시작할 수 있어요.")
            else:
                if (st.session_state.current_q3 is None) or st.session_state.solved_current_q3:
                    remaining = [w for w in st.session_state.remaining_q3 if w not in st.session_state.solved_q3]
                    if not remaining:
                        st.session_state.completed_q3 = True
                    else:
                        target_word = random.choice(remaining)
                        row = cur_df3[cur_df3["Word"] == target_word].iloc[0]
                        meaning = str(row["Meaning"])
                        pool_words = [str(w) for w in cur_df3["Word"].tolist()]
                        options = make_k_options_including_correct(target_word, pool_words, k=5)
                        st.session_state.current_q3 = {
                            "word": target_word,
                            "meaning": meaning,
                            "options": options
                        }
                        st.session_state.user_choice_q3 = None
                        st.session_state.answered_q3 = False
                        st.session_state.solved_current_q3 = False

    with colF:
        if st.button("🔁 초기화 (Reset)", key="reset_q3"):
            reset_q3_all()
            st.session_state.remaining_q3 = list(cur_df3["Word"])
            st.success("이 세트를 초기화했습니다.")

    if st.session_state.completed_q3:
        st.success("🎉 이 세트의 10개 단어(뜻 맞히기)를 모두 완료했습니다! 다시 연습하려면 ‘초기화’를 누르세요.")

    if st.session_state.current_q3 and not st.session_state.completed_q3:
        q3 = st.session_state.current_q3
        st.markdown("**Q:** 다음 뜻(Meaning)에 알맞은 단어를 고르세요.")
        st.markdown(f"<div style='font-size:16px; line-height:1.6'><b>뜻:</b> {q3['meaning']}</div>", unsafe_allow_html=True)
        st.write("")
        st.session_state.user_choice_q3 = st.radio(
            "정답을 선택하세요:",
            q3["options"],
            index=None,
            key="mcq_choice_q3",
        )

        if st.button("정답 확인 (Show me the answer)", key="check_q3"):
            if st.session_state.user_choice_q3 is None:
                st.warning("먼저 보기를 선택하세요.")
            else:
                st.session_state.answered_q3 = True
                if st.session_state.user_choice_q3 == q3["word"]:
                    st.success("Correct ✅")
                    st.session_state.solved_q3.add(q3["word"])
                    st.session_state.solved_current_q3 = True
                    remaining_after = [w for w in st.session_state.remaining_q3 if w not in st.session_state.solved_q3]
                    if not remaining_after:
                        st.session_state.completed_q3 = True
                        st.balloons()
                else:
                    st.error(f"Incorrect ❌  |  정답: {q3['word']} (다시 시도하세요. ‘새 문제 시작’을 눌러도 현재 문항이 유지됩니다.)")

    if st.session_state.remaining_q3:
        st.caption(f"진행 상황: {len(st.session_state.solved_q3)}/{len(st.session_state.remaining_q3)} 완료")

# -------------------------------------------------
# Tab 2: 문장 속 단어 (MCQ)
# -------------------------------------------------
with tab2:
    st.markdown("#### 1. 세트 선택")
    idx1 = _safe_index(set_names, st.session_state.selected_set)
    set_choice = st.selectbox(
        "Choose a word set to practice:",
        set_names,
        index=idx1,
        key="set_select_q1",
    )

    if set_choice != st.session_state.selected_set:
        st.session_state.selected_set = set_choice
        # rebuild remaining lists for all tabs
        cur_df = sets[st.session_state.selected_set].copy()
        st.session_state.remaining_q1 = list(cur_df["Word"])
        st.session_state.remaining_q2 = list(cur_df["Word"])
        st.session_state.remaining_q3 = list(cur_df["Word"])
        reset_all_for_set_change()

    cur_df = sets[st.session_state.selected_set].copy()
    if not st.session_state.remaining_q1:
        st.session_state.remaining_q1 = list(cur_df["Word"])

    st.markdown("#### 2. 연습 시작")
    colA, colB = st.columns([1, 1])

    with colA:
        if st.button("🍅 Start / Continue", key="start_q1"):
            if st.session_state.completed_q1:
                st.info("이 세트의 모든 문항을 완료했습니다. 🔒 ‘초기화’로 다시 시작할 수 있어요.")
            else:
                if (st.session_state.current_q1 is None) or st.session_state.solved_current_q1:
                    remaining = [w for w in st.session_state.remaining_q1 if w not in st.session_state.solved_q1]
                    if not remaining:
                        st.session_state.completed_q1 = True
                    else:
                        target_word = random.choice(remaining)
                        row = cur_df[cur_df["Word"] == target_word].iloc[0]
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
                        st.session_state.solved_current_q1 = False

    with colB:
        if st.button("🔁 초기화 (Reset)", key="reset_q1"):
            reset_q1_all()
            st.session_state.remaining_q1 = list(cur_df["Word"])
            st.success("이 세트를 초기화했습니다.")

    if st.session_state.completed_q1:
        st.success("🎉 이 세트의 10개 단어를 모두 완료했습니다! 다시 연습하려면 ‘초기화’를 누르세요.")

    if st.session_state.current_q1 and not st.session_state.completed_q1:
        q = st.session_state.current_q1
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
                    st.session_state.solved_q1.add(q["word"])
                    st.session_state.solved_current_q1 = True
                    remaining_after = [w for w in st.session_state.remaining_q1 if w not in st.session_state.solved_q1]
                    if not remaining_after:
                        st.session_state.completed_q1 = True
                        st.balloons()
                else:
                    st.error(f"Incorrect ❌  |  정답: {q['word']} (다시 시도하세요. ‘새 문제 시작’을 눌러도 현재 문항이 유지됩니다.)")

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

    if st.session_state.remaining_q1:
        st.caption(f"진행 상황: {len(st.session_state.solved_q1)}/{len(st.session_state.remaining_q1)} 완료")

# -------------------------------------------------
# Tab 3: 듣고 스펠링 (대소문자/공백/문장부호 무시)
# -------------------------------------------------
with tab3:
    st.markdown("#### 1. 세트 선택")
    idx2 = _safe_index(set_names, st.session_state.selected_set)
    set_choice2 = st.selectbox(
        "Choose a word set to practice:",
        set_names,
        index=idx2,
        key="set_select_q2",
    )
    if set_choice2 != st.session_state.selected_set:
        st.session_state.selected_set = set_choice2
        cur_df2 = sets[st.session_state.selected_set].copy()
        st.session_state.remaining_q1 = list(cur_df2["Word"])
        st.session_state.remaining_q2 = list(cur_df2["Word"])
        st.session_state.remaining_q3 = list(cur_df2["Word"])
        reset_all_for_set_change()

    cur_df2 = sets[st.session_state.selected_set].copy()
    if not st.session_state.remaining_q2:
        st.session_state.remaining_q2 = list(cur_df2["Word"])

    st.markdown("#### 2. 연습 시작")
    colC, colD = st.columns([1, 1])
    with colC:
        if st.button("🍅 Start / Continue", key="start_q2"):
            if st.session_state.completed_q2:
                st.info("이 세트의 모든 문항을 완료했습니다. 🔒 ‘초기화’로 다시 시작할 수 있어요.")
            else:
                if (st.session_state.current_q2 is None) or st.session_state.solved_current_q2:
                    remaining = [w for w in st.session_state.remaining_q2 if w not in st.session_state.solved_q2]
                    if not remaining:
                        st.session_state.completed_q2 = True
                    else:
                        target_word = random.choice(remaining)
                        audio_bytes = tts_cached(target_word, lang="en")  # <- cached TTS
                        st.session_state.current_q2 = {"word": target_word}
                        st.session_state.audio_bytes_q2 = audio_bytes
                        st.session_state.user_spelling = ""
                        st.session_state.answered_q2 = False
                        st.session_state.solved_current_q2 = False

    with colD:
        if st.button("🔁 초기화 (Reset)", key="reset_q2"):
            reset_q2_all()
            st.session_state.remaining_q2 = list(cur_df2["Word"])
            st.success("이 세트를 초기화했습니다.")

    if st.session_state.completed_q2:
        st.success("🎉 이 세트의 10개 단어(듣고 쓰기)를 모두 완료했습니다! 다시 연습하려면 ‘초기화’를 누르세요.")

    if st.session_state.current_q2 and not st.session_state.completed_q2:
        q2 = st.session_state.current_q2

#        if st.session_state.audio_bytes_q2:
#            st.audio(st.session_state.audio_bytes_q2, format="audio/mp3")
        if st.session_state.audio_bytes_q2:
#            st.markdown(audio_html(st.session_state.audio_bytes_q2), unsafe_allow_html=True)
            st.audio(st.session_state.audio_bytes_q2, format="audio/mp3")


        else:
            st.warning("오디오 로드에 문제가 발생했습니다. 다시 시작해 주세요.")

    
        st.write("")
        st.markdown("**Q:** 들은 단어(또는 어구)의 스펠링을 입력하세요.")
        st.session_state.user_spelling = st.text_input(
            "정답 입력:",
            value=st.session_state.user_spelling,
            key="spelling_input",
            placeholder="예: be good at",
        )

        if st.button("정답 확인 (Check spelling)", key="check_q2"):
            user_norm = normalize_answer(st.session_state.user_spelling)
            correct_norm = normalize_answer(q2["word"])
            st.session_state.answered_q2 = True
            if user_norm and user_norm == correct_norm:
                st.success("Correct ✅")
                st.session_state.solved_q2.add(q2["word"])
                st.session_state.solved_current_q2 = True
                remaining_after = [w for w in st.session_state.remaining_q2 if w not in st.session_state.solved_q2]
                if not remaining_after:
                    st.session_state.completed_q2 = True
                    st.balloons()
            else:
                st.error(f"Incorrect ❌  |  정답: {q2['word']} (다시 시도하세요. ‘새 문제 시작’을 눌러도 현재 문항이 유지됩니다.)")

    if st.session_state.remaining_q2:
        st.caption(f"진행 상황: {len(st.session_state.solved_q2)}/{len(st.session_state.remaining_q2)} 완료")
