import streamlit as st
from langchain_core.messages import HumanMessage


def render_chat_interface():
    st.title("Chat Interface")

    if "command_manager" not in st.session_state:
        print("Error: CommandManager not found in session state.")

    if "messages" not in st.session_state:
        st.session_state.messages = []


    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


    if prompt := st.chat_input("Type your message here"):
        with st.chat_message("user"):
            st.markdown(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

        if prompt.lower() == 'exit':
            st.stop()

        if prompt.startswith('/'):
            # command

            command_manager = st.session_state.command_manager
            response = command_manager.execute_command(prompt)

            if response:
                with st.chat_message("assistant"):
                    st.markdown(response)

                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                with st.chat_message("assistant"):
                    st.markdown("I'm sorry, I couldn't process that command.")

                st.session_state.messages.append(
                    {"role": "assistant", "content": "I'm sorry, I couldn't process that command."}
                )
        else:
            # normal message processing
            tool_agent = st.session_state.tool_agent
            response = tool_agent.invoke({"messages": [HumanMessage(content=prompt)]}, {"thread_id": 1})
            response = response["messages"][-1].content

            with st.chat_message("assistant"):
                st.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})