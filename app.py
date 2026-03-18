import streamlit as st
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv

st.set_page_config(
    page_title="VocalHire: AI Mock Interviewer",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

load_dotenv()

def get_secret(key_name, default_val=""):
    """Checks Streamlit secrets first, then local environment variables."""
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name, default_val)

# Changed from OPENAI_API_KEY to GROQ_API_KEY
GROQ_API_KEY = get_secret("GROQ_API_KEY")
MURF_API_KEY = get_secret("MURF_API_KEY")
MURF_VOICE_ID = get_secret("MURF_VOICE_ID", "en-US-marcus") 

SYSTEM_PROMPT = """You are a strict but fair HR manager at a top tech company. 
Conduct a mock interview with the user. Ask one question at a time. 
Keep your questions under 2 sentences. Wait for their response."""

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

def generate_murf_audio(text):
    """Generates audio from text using Murf AI's Falcon TTS model."""
    MURF_API_URL = "https://api.murf.ai/v1/speech/generate"
    
    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "voiceId": MURF_VOICE_ID,       
        "text": text,                    
        "model": "FALCON"              
    }
    
    try:
        response = requests.post(
            MURF_API_URL,
            headers=headers,
            json=payload,
            timeout=30 
        )
        
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Murf API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Error connecting to Murf AI: {str(e)}")
        return None

def get_openai_response(messages):
    """Gets a response using Groq's high-speed Llama 3 model."""
    try:
        # Changed the setup to point to Groq's servers
        client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        response = client.chat.completions.create(
            model="llama3-8b-8192", 
            messages=messages, # Uses the passed messages list
            max_tokens=150,  
            temperature=0.7  
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Groq API Error: {str(e)}")
        return None


st.title("🎙️ VocalHire: AI Mock Interviewer")
st.subheader("Powered by Groq & Murf Falcon TTS")
st.divider()

for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.write(message["content"])

if len(st.session_state.messages) == 1: 
    if st.button("🚀 Start Interview", type="primary"):
        with st.spinner("Interviewer is joining the room..."):
            ai_response = get_openai_response(st.session_state.messages)
            
            if ai_response:
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
                with st.chat_message("assistant"):
                    st.write(ai_response)
                
                audio_bytes = generate_murf_audio(ai_response)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                
user_input = st.chat_input("Type your answer here...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    
    with st.spinner("🤔 Thinking..."):
        ai_response = get_openai_response(st.session_state.messages)
    
    if ai_response:
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        with st.chat_message("assistant"):
            st.write(ai_response)
        
        with st.spinner("🎧 Generating audio..."):
            audio_bytes = generate_murf_audio(ai_response)
        
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        else:
            st.warning("Audio generation failed. Showing text only.")

with st.sidebar:
    st.header("ℹ️ About")
    st.info("VocalHire is an AI-powered mock interview application using Groq (Llama 3) and Murf Falcon TTS.")
    
    st.header("🔑 API Status")
    if GROQ_API_KEY:
        st.success("✅ Groq API Key: Loaded")
    else:
        st.error("❌ Groq API Key: Missing")
    
    if MURF_API_KEY:
        st.success("✅ Murf API Key: Loaded")
    else:
        st.error("❌ Murf API Key: Missing")
    
    if st.button("🔄 Reset Interview"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()
