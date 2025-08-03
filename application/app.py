import streamlit as st 
import logging
import sys
import os
import agent
import chat
import asyncio

logging.basicConfig(
    level=logging.INFO,  # Default to INFO level
    format='%(filename)s:%(lineno)d | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("streamlit")

os.environ["DEV"] = "true"  # Skip user confirmation of get_user_input

# title
st.set_page_config(page_title='Hyun', page_icon=None, layout="centered", initial_sidebar_state="auto", menu_items=None)

mode_descriptions = {
    "Hyun Agent": [
        "MCP를 도구로 활용하는 Agent를 이용합니다."
    ]
}

with st.sidebar:
    st.title("🔮 Menu")
    
    st.markdown(
        "Strands와 MCP를 이용하여 똑똑한 Agent를 구현합니다." 
        "상세한 코드는 [Github](https://github.com/kyopark2014/woo-project)을 참조하세요."
    )

    st.subheader("🐱 대화 형태")
    
    # radio selection
    mode = st.radio(
        label="원하는 대화 형태를 선택하세요. ",options=["Hyun Agent"], index=0
    )   
    st.info(mode_descriptions[mode][0])
    
    # model selection box
    modelName = st.selectbox(
        '🖊️ 사용 모델을 선택하세요',
        ('Claude 4 Opus', 'Claude 4 Sonnet', 'Claude 3.7 Sonnet', 'Claude 3.5 Sonnet', 'Claude 3.0 Sonnet', 'Claude 3.5 Haiku'), index=2
    )

    # debug checkbox
    select_debugMode = st.checkbox('Debug Mode', value=True)
    debugMode = 'Enable' if select_debugMode else 'Disable'

    chat.update(modelName, debugMode)

    st.success(f"Connected to {modelName}", icon="💚")
    clear_button = st.button("대화 초기화", key="clear")

st.title('🔮 '+ mode)

if clear_button or "messages" not in st.session_state:
    st.session_state.messages = []        
    
    st.session_state.greetings = False
    st.rerun()  

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.greetings = False

# Display chat messages from history on app rerun
def display_chat_messages() -> None:
    """Print message history"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

display_chat_messages()

# Greet user
if not st.session_state.greetings:
    with st.chat_message("assistant"):
        intro = "아마존 베드락을 이용하여 주셔서 감사합니다. Agent를 이용해 향상된 대화를 즐기실 수 있습니다."
        st.markdown(intro)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": intro})
        st.session_state.greetings = True

if clear_button or "messages" not in st.session_state:
    st.session_state.messages = []        
    uploaded_file = None
    
    st.session_state.greetings = False
    chat.initiate()
    st.rerun()    

# Always show the chat input
if prompt := st.chat_input("메시지를 입력하세요."):
    with st.chat_message("user"):  # display user message in chat message container
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})  # add user message to chat history
    prompt = prompt.replace('"', "").replace("'", "")
    logger.info(f"prompt: {prompt}")

    with st.chat_message("assistant"):        
        sessionState = ""            
        
        with st.status("thinking...", expanded=True, state="running") as status:            
            if mode == "Hyun Agent":            
                containers = {
                    "tools": st.empty(),
                    "status": st.empty(),
                    "notification": [st.empty() for _ in range(500)]
                }                
                response = asyncio.run(agent.run_agent(query=prompt, containers=containers))
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response
        })
            