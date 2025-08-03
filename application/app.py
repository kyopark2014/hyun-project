import streamlit as st 
import logging
import sys
import os
import agent
import chat
import asyncio
import multi_mcp_agent

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
        "상세한 코드는 [Github](https://github.com/kyopark2014/hyun-project)을 참조하세요."
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
        ('Claude 4 Opus', 'Claude 4 Sonnet', 'Claude 3.7 Sonnet', 'Claude 3.5 Sonnet', 'Claude 3.0 Sonnet', 'Claude 3.5 Haiku'), index=1
    )

    # debug checkbox
    select_debugMode = st.checkbox('Debug Mode', value=True)
    debugMode = 'Enable' if select_debugMode else 'Disable'

    chat.update(modelName, debugMode)

    # selecttion of single or multi mcp agent
    mcp_agent_mode = st.radio(
        label="MCP Agent 동작방식을 선택하세요. ",options=["Single", "Multiple"], index=1
    )

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
    """Print message history
    @returns None
    """
    for i, message in enumerate(st.session_state.messages):
        logger.info(f"메시지 {i+1} 표시: role={message['role']}, images={message.get('images', [])}")
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "images" in message and message["images"]:
                logger.info(f"메시지 {i+1}에서 이미지 {len(message['images'])}개 발견")
                for j, url in enumerate(message["images"]):
                    logger.info(f"메시지 {i+1} 이미지 {j+1} URL: {url}")
                    try:
                        file_name = url[url.rfind('/')+1:] if '/' in url else url
                        st.image(url, caption=file_name, use_container_width=True)
                        logger.info(f"메시지 {i+1} 이미지 {j+1} 표시 성공")
                    except Exception as e:
                        logger.error(f"메시지 {i+1} 이미지 {j+1} 표시 오류: {e}")
                        st.error(f"이미지를 표시할 수 없습니다: {url}")
            else:
                logger.info(f"메시지 {i+1}에 이미지가 없습니다.")

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
            containers = {
                "tools": st.empty(),
                "status": st.empty(),
                "notification": [st.empty() for _ in range(500)]
            }  
                   
            image_url = None
            if mode == "Hyun Agent" and mcp_agent_mode == "Single":                                          
                response = asyncio.run(agent.run_agent(query=prompt, containers=containers))
            else:
                response, image_url = asyncio.run(multi_mcp_agent.run_agent(query=prompt, containers=containers))

            logger.info(f"image_url type: {type(image_url)}, value: {image_url}")
            assistant_message = {
                "role": "assistant", 
                "content": response,
                "images": image_url if image_url else []
            }
            st.session_state.messages.append(assistant_message)
            
            if image_url:
                if isinstance(image_url, list):
                    valid_image_urls = [url for url in image_url if url and url.strip()]
                    if not valid_image_urls:
                        logger.info("유효한 이미지 URL이 없습니다.")
                        image_url = None
                    else:
                        image_url = valid_image_urls
                elif not image_url or not image_url.strip():
                    logger.info("유효한 이미지 URL이 없습니다.")
                    image_url = None
                
                if image_url:
                    logger.info(f"이미지 표시 시작: {image_url}")
                    if isinstance(image_url, list):
                        logger.info(f"이미지 리스트 길이: {len(image_url)}")
                        for i, url in enumerate(image_url):
                            logger.info(f"이미지 {i+1} URL: {url}")
                            try:
                                file_name = url[url.rfind('/')+1:] if '/' in url else url
                                st.image(url, caption=file_name, use_container_width=True)
                                logger.info(f"이미지 {i+1} 표시 성공")
                            except Exception as e:
                                logger.error(f"이미지 {i+1} 표시 오류: {e}")
                                st.error(f"이미지를 표시할 수 없습니다: {url}")
                    else:
                        logger.info(f"단일 이미지 URL: {image_url}")
                        try:
                            file_name = image_url[image_url.rfind('/')+1:] if '/' in image_url else image_url
                            st.image(image_url, caption=file_name, use_container_width=True)
                            logger.info("단일 이미지 표시 성공")
                        except Exception as e:
                            logger.error(f"단일 이미지 표시 오류: {e}")
                            st.error(f"이미지를 표시할 수 없습니다: {image_url}")
            else:
                logger.info("표시할 이미지가 없습니다.")
            