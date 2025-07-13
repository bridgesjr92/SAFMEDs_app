import pandas as pd
import random
import streamlit as st
import datetime
import os

# === Load Excel ===
@st.cache_data
def load_data():
    file_path = "ABA624 Measurement and Design SAFMED DATA.xlsx"
    section_c = pd.read_excel(file_path, sheet_name="624 - section C").dropna()
    section_d = pd.read_excel(file_path, sheet_name="624 - section D").dropna()
    section_c.columns = ["Term", "Definition"]
    section_d.columns = ["Term", "Definition"]
    return {
        "Section C": list(section_c.itertuples(index=False, name=None)),
        "Section D": list(section_d.itertuples(index=False, name=None))
    }

data_sets = load_data()
SCORE_FILE = "scores.csv"

# === Session State ===
if "active" not in st.session_state:
    st.session_state.active = False
    st.session_state.score = 0
    st.session_state.attempted = 0
    st.session_state.start_time = None
    st.session_state.duration = 60
    st.session_state.term_list = []
    st.session_state.current_term = None
    st.session_state.correct_def = ""
    st.session_state.shown_def = ""
    st.session_state.is_true = True

# === Sidebar Config ===
st.sidebar.header("SAFMEDS Settings")
selected_set = st.sidebar.selectbox("Choose Study Set", list(data_sets.keys()))
duration = st.sidebar.radio("Session Duration (sec)", [60, 90, 120], index=0)
start_btn = st.sidebar.button("Start / Restart Session")

# === Start Session ===
if start_btn:
    st.session_state.active = True
    st.session_state.score = 0
    st.session_state.attempted = 0
    st.session_state.start_time = datetime.datetime.now()
    st.session_state.duration = duration
    st.session_state.term_list = data_sets[selected_set]

# === Function: Load Next Term ===
def next_card():
    term, correct_def = random.choice(st.session_state.term_list)
    is_true = random.choice([True, False])

    if is_true:
        shown_def = correct_def
    else:
        wrong_defs = [d for t, d in st.session_state.term_list if t != term]
        shown_def = random.choice(wrong_defs)

    st.session_state.current_term = term
    st.session_state.correct_def = correct_def
    st.session_state.shown_def = shown_def
    st.session_state.is_true = is_true

# === Function: Save Score ===
def save_score():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    percent = (st.session_state.score / st.session_state.attempted * 100) if st.session_state.attempted > 0 else 0
    row = {
        "Date": now,
        "Set": selected_set,
        "Time (s)": st.session_state.duration,
        "Score": st.session_state.score,
        "Attempted": st.session_state.attempted,
        "Percent": f"{percent:.1f}"
    }
    df = pd.DataFrame([row])
    if os.path.exists(SCORE_FILE):
        df.to_csv(SCORE_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(SCORE_FILE, index=False)

# === Display Scores ===
if os.path.exists(SCORE_FILE):
    st.subheader("📊 Recent Scores")
    score_df = pd.read_csv(SCORE_FILE).tail(5)
    st.dataframe(score_df, use_container_width=True)

# === Main Game Logic ===
if st.session_state.active:
    elapsed = (datetime.datetime.now() - st.session_state.start_time).total_seconds()

    if elapsed >= st.session_state.duration:
        st.session_state.active = False
        percent = (st.session_state.score / st.session_state.attempted * 100) if st.session_state.attempted > 0 else 0
        st.success(f"Session Complete!\nScore: {st.session_state.score} / {st.session_state.attempted} ({percent:.1f}%)")

        if st.button("Save This Score"):
            save_score()
            st.experimental_rerun()
    else:
        if st.session_state.current_term is None:
            next_card()

        st.markdown(f"### 🟥 Term: {st.session_state.current_term}")
        st.markdown(f"### 🟩 Definition: {st.session_state.shown_def}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("True (T)"):
                st.session_state.attempted += 1
                if st.session_state.is_true:
                    st.session_state.score += 1
                    st.success("Correct!")
                else:
                    st.error(f"Incorrect. Correct definition: {st.session_state.correct_def}")
                next_card()

        with col2:
            if st.button("False (F)"):
                st.session_state.attempted += 1
                if not st.session_state.is_true:
                    st.session_state.score += 1
                    st.success("Correct!")
                else:
                    st.error(f"Incorrect. Correct definition: {st.session_state.correct_def}")
                next_card()

        st.info(f"⏱️ Time left: {int(st.session_state.duration - elapsed)} seconds")
        st.text(f"Score: {st.session_state.score} / {st.session_state.attempted}")
