
import os
from pathlib import Path
import uuid

import streamlit as st
from dotenv import load_dotenv
from groq import (
    Groq,
    AuthenticationError,
    RateLimitError,
    APIConnectionError,
    APIStatusError,
)

# -----------------------------------
# 1. Page Configuration
# -----------------------------------
st.set_page_config(
    page_title="Yaswanth AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------
# 2. Load Groq API Key
# -----------------------------------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "openai/gpt-oss-120b"

# -----------------------------------
# 3. Custom CSS
# -----------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f7f7f8;
    }

    [data-testid="stSidebar"] {
        background-color: #202123;
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    .main-heading {
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        color: #202123;
        padding: 12px;
    }

    .sub-heading {
        text-align: center;
        color: #6b7280;
        margin-bottom: 25px;
    }

    .footer {
        text-align: center;
        color: #777;
        font-size: 13px;
        padding: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------
# 4. Initialize Chat History
# -----------------------------------
if "chats" not in st.session_state:
    chat_id = str(uuid.uuid4())

    st.session_state.chats = {
        chat_id: {
            "title": "New Chat",
            "messages": [],
        }
    }
    st.session_state.active_chat_id = chat_id

if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = next(iter(st.session_state.chats))

if st.session_state.active_chat_id not in st.session_state.chats:
    st.session_state.active_chat_id = next(iter(st.session_state.chats))


# -----------------------------------
# 5. Chat Functions
# -----------------------------------
def create_new_chat():
    new_id = str(uuid.uuid4())

    st.session_state.chats[new_id] = {
        "title": "New Chat",
        "messages": [],
    }

    st.session_state.active_chat_id = new_id


def clear_current_chat():
    chat = st.session_state.chats[st.session_state.active_chat_id]
    chat["messages"] = []
    chat["title"] = "New Chat"


def get_ai_response(messages):
    client = Groq(api_key=GROQ_API_KEY)

    system_message = {
        "role": "system",
        "content": (
            "You are a helpful AI assistant similar to ChatGPT. "
            "Explain topics in simple English when appropriate. "
            "Help beginners understand programming, technology, "
            "education, and general topics. "
            "Give clear, accurate, and polite answers."
        ),
    }

    conversation = [system_message] + messages

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=conversation,
        temperature=0.7,
    )

    return response.choices[0].message.content


# -----------------------------------
# 6. Sidebar
# -----------------------------------
with st.sidebar:
    st.markdown("## 🤖 Yaswanth AI")

    if st.button("➕ New Chat", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.divider()
    st.markdown("### 💬 Chat History")

    chat_ids = list(st.session_state.chats.keys())
    chat_ids.reverse()

    for chat_id in chat_ids:
        chat_title = st.session_state.chats[chat_id]["title"]

        if st.button(
            f"💬 {chat_title}",
            key=f"history_{chat_id}",
            use_container_width=True,
        ):
            st.session_state.active_chat_id = chat_id
            st.rerun()

    st.divider()

    if st.button("🗑️ Clear Current Chat", use_container_width=True):
        clear_current_chat()
        st.rerun()

    st.markdown("---")
    st.caption("Built with Python, Streamlit and Groq")


# -----------------------------------
# 7. Main Interface
# -----------------------------------
st.markdown(
    '<div class="main-heading">🤖 Yaswanth AI Chatbot</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="sub-heading">'
    'Your AI assistant for learning and exploring'
    '</div>',
    unsafe_allow_html=True,
)

st.divider()

active_chat = st.session_state.chats[
    st.session_state.active_chat_id
]

messages = active_chat["messages"]

# -----------------------------------
# 8. Welcome Message
# -----------------------------------
if not messages:
    st.markdown("### 👋 Hello! How can I help you today?")
    st.write(
        "Ask questions about Python, Artificial Intelligence, "
        "Machine Learning, programming, studies, or other topics."
    )

# -----------------------------------
# 9. Display Previous Messages
# -----------------------------------
for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -----------------------------------
# 10. Chat Input
# -----------------------------------
user_prompt = st.chat_input("Message Yaswanth AI...")

if user_prompt:
    # Save user message
    messages.append({
        "role": "user",
        "content": user_prompt,
    })

    # Use the first message as the chat title
    if active_chat["title"] == "New Chat":
        active_chat["title"] = user_prompt[:35]

    # Display the user message
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Check API key
    if not GROQ_API_KEY:
        st.error(
            "Groq API key is missing. "
            "Please configure your .env file."
        )

    else:
        try:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    answer = get_ai_response(messages)

                if not answer:
                    answer = "I could not generate a response. Please try again."

                st.markdown(answer)

            # Save AI response
            messages.append({
                "role": "assistant",
                "content": answer,
            })

        except AuthenticationError:
            st.error(
                "Invalid API key. Please check your Groq API key."
            )

        except RateLimitError:
            st.error(
                "API rate limit reached. Please wait and try again."
            )

        except APIConnectionError:
            st.error(
                "Connection failed. Please check your internet connection."
            )

        except APIStatusError as error:
            st.error(f"Groq API Error: HTTP {error.status_code}")

            if error.status_code == 404:
                st.warning(
                    "The selected model may be unavailable. "
                    "Check the current Groq model list."
                )
            else:
                st.caption(str(error))

        except Exception as error:
            st.error("An unexpected error occurred.")
            st.code(str(error))

# -----------------------------------
# 11. Footer
# -----------------------------------
st.divider()

st.markdown(
    '<div class="footer">'
    'Yaswanth AI Chatbot | Python + Streamlit + Groq API'
    '</div>',
    unsafe_allow_html=True,
)