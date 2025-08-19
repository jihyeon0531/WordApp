import streamlit as st

st.set_page_config(page_title="Test App")
st.title("Hello, Streamlit!")

tab1, tab2 = st.tabs(["Intro", "Table"])
with tab1:
    st.write("Welcome to the app.")
with tab2:
    st.write("This is a table.")

