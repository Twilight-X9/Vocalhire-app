import streamlit as st
from openai import OpenAI
import requests
import os
import base64
from dotenv import load_dotenv

# --- Configuration ---
st.set_page_config(
    page_title="VocalHire: AI Mock Interviewer",
    page_icon="🎙️",
    layout="centered"
)

load_dotenv()

def get_secret(key_name, default_val=""):
    """Checks Streamlit secrets first, then local environment variables."""
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name, default_val)

# Decide here whether you are using OpenAI or Groq
# I've defaulted to OpenAI logic based on your variable names
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
MURF_API_KEY = get_secret("MURF_API_KEY")
MURF_VOICE_ID = get_secret("MURF_VOICE_ID", "en-US-marcus")

SYSTEM_PROMPT = """You are a strict but fair HR manager at a top tech company. 
Conduct a mock interview with the user. Ask one question at a time. 
Keep your questions under 2 sentences. Wait for their response."""

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# --- Logic Functions ---

def generate_murf_audio(text):
    """Generates audio from text using Murf AI."""
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
        response = requests.post(MURF_API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            # Murf usually returns a publicly accessible URL in 'encodedAudio' or 'audioFile'
            audio_url = data.get("audioFile")
            if audio_url:
                audio_content = requests.get(audio_url).content
                return audio_content
        else:
            st.error(f"Murf API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error connecting to Murf AI: {str(e)}")
        return None

def get_openai_response(messages):
    """Gets a response from the LLM."""
    try:
        # Note: If using Groq, use the Groq API Key and base_url here.
        # If using standard OpenAI, remove the base_url.
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Change to "llama3-8b-8192" if using Groq
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"LLM Error: {str(e)}")
        return None

# --- UI Layout ---
st.title("🎙️ VocalHire: AI Mock Interviewer")
st.subheader("Powered by Murf Falcon TTS")
st.divider()

# Display Chat History
for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.write(message["content"])

# --- Interview Flow ---

# Start Button (only shows if no messages other than system exist)
if len(st.session_state.messages) == 1:
    if st.button("🚀 Start Interview", type="primary"):
        with st.spinner("Interviewer is joining..."):
            ai_response = get_openai_response(st.session_state.messages)
            if ai_response:
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                st.rerun()

# Handle User Input
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

# --- Sidebar ---
with st.sidebar:
    st.header("ℹ️ About")
    st.info("VocalHire uses LLMs to simulate real-world pressure.")
    
    if st.button("🔄 Reset Interview"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()
