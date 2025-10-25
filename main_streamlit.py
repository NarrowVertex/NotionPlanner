import streamlit as st
from command import CommandManager
from streamlit_ui.chat_ui import render_chat_interface


if "command_manager" not in st.session_state:
    st.session_state.command_manager = CommandManager()

render_chat_interface()