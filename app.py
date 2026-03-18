import streamlit as st
from groq import Groq
import requests
import os
import base64
from dotenv import load_dotenv


st.set_page_config(
    page_title="VocalHire",
    page_icon="🎙️",
    layout="centered"
)

load_dotenv()

def get_secret(key_name, default_val=""):
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name, default_val)

GROQ_API_KEY = get_secret("GROQ_API_KEY")
MURF_API_KEY = get_secret("MURF_API_KEY")
MURF_VOICE_ID = get_secret("MURF_VOICE_ID", "en-US-marcus")


client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a strict but fair HR manager at a top tech company. 
Conduct a mock interview with the user. Ask one question at a time. 
Keep your questions under 2 sentences. Wait for their response."""


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]



def generate_murf_audio(text):
    """Generates audio bytes using Murf AI Falcon model."""
    url = "https://api.murf.ai/v1/speech/generate"
    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "voiceId": MURF_VOICE_ID,
        "text": text,
        "model": "FALCON",
        "encodeAsBase64": True 
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
          
            data = response.json()
            audio_base64 = data.get("encodedAudio")
            if audio_base64:
                return base64.b64decode(audio_base64)
        else:
            st.error(f"Murf Error: {response.text}")
            return None
    except Exception as e:
        st.error(f"TTS Connection Failed: {e}")
        return None

def get_groq_response(messages):
    """Fetches response from Groq using Llama 3.3 70B."""
    try:
        chat_completion = client.chat.completions.create(
            
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"Groq Inference Error: {e}")
        return None


st.title("🎙️ VocalHire: Ai Mock Interviewer")
st.caption("Powered By Murf Falcon TTS")
st.divider()


for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.write(message["content"])

if len(st.session_state.messages) == 1:
    if st.button("🚀 Start Interview", type="primary", use_container_width=True):
        with st.spinner("Interviewer is entering the room..."):
            ai_msg = get_groq_response(st.session_state.messages)
            if ai_msg:
                st.session_state.messages.append({"role": "assistant", "content": ai_msg})
                st.rerun()


user_input = st.chat_input("Your answer...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

if st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("HR is thinking..."):
            ai_msg = get_groq_response(st.session_state.messages)
            if ai_msg:
                st.write(ai_msg)
                st.session_state.messages.append({"role": "assistant", "content": ai_msg})
                
                audio_data = generate_murf_audio(ai_msg)
                if audio_data:
                    st.audio(audio_data, format="audio/mp3", autoplay=True)

with st.sidebar:
    st.header("⚙️ Settings")
    if st.button("🔄 Reset Interview", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()
    
    st.divider()
    st.write(f"**API Status:**")
    st.success("Groq: Online") if GROQ_API_KEY else st.error("Groq: Missing Key")
    st.success("Murf: Online") if MURF_API_KEY else st.error("Murf: Missing Key")
