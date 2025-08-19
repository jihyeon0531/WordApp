import streamlit as st

st.write("Welcome to Jihyeon Teacher's App Page")
st.caption("Since Aug 15, 2025")

# Image links
main_image_url = "https://github.com/jihyeon0531/WordApp/raw/main/images/welcome2.png"
qr_image_url = "https://github.com/jihyeon0531/WordApp/raw/main/images/appQR.png"

# Center the images
st.markdown(
    f"""
    <div style="text-align: center;">
        <img src="{main_image_url}" width="300"><br><br>
        <img src="{qr_image_url}" width="180">
    </div>
    """,
    unsafe_allow_html=True
)
