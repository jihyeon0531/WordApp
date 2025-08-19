import streamlit as st

st.write("Welcome to Jihyeon Teacher's App Page")
st.caption("Since Aug 15, 2025")

# Image links
main_image_url = "https://github.com/jihyeon0531/WordApp/raw/main/images/welcome2.png"
qr_image_url = "https://github.com/jihyeon0531/WordApp/raw/main/images/appQR.png"

# Use columns to center images
col1, col2, col3 = st.columns([1, 2, 1])  # middle column bigger

with col1:
    st.image(main_image_url, width=500, caption="Welcome Image")  # Expand button appears
with col3:
    st.image(qr_image_url, width=50, caption="QR Code")  # Expand button appears

