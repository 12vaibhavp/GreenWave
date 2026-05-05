import streamlit as st
import os

st.title("🚦 AI Traffic Signal System")

if st.button("Run Fixed"):
    os.system("python fixed_control.py")

if st.button("Run Adaptive"):
    os.system("python adaptive_control.py")

if st.button("Run Q-Learning"):
    os.system("python qlearning_control.py")

if st.button("Show Graph"):
    os.system("python compare_result.py")