import streamlit as st
from command import CommandManager
from streamlit_ui.chat_ui import render_chat_interface
from notion import Planner, Task
from agent import get_tool_agent


if "command_manager" not in st.session_state:
    st.session_state.command_manager = CommandManager()

if "tool_agent" not in st.session_state:
    st.session_state.tool_agent = get_tool_agent(Planner(), Task)

render_chat_interface()