import streamlit as st
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv

# ============================================================================
# 1. CONFIGURE STREAMLIT PAGE
# ============================================================================
st.set_page_config(
    page_title="VocalHire: AI Mock Interviewer",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# 2. SMART API KEY LOADER
# ============================================================================
load_dotenv()

def get_secret(key_name, default_val=""):
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name, default_val)

GROQ_API_KEY = get_secret("GROQ_API_KEY") 
MURF_API_KEY = get_secret("MURF_API_KEY")
MURF_VOICE_ID = get_secret("MURF_VOICE_ID", "en-US-marcus")

# ============================================================================
# 3. SYSTEM PROMPT FOR THE HR MANAGER
# ============================================================================
SYSTEM_PROMPT = """You are a strict but fair HR manager at a top tech company. 
Conduct a mock interview with the user. Ask one question at a time. 
Keep your questions under 2 sentences. Wait for their response."""

if "messages" not in st.session_state:
    st.session_state.messages =[
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# ============================================================================
# 4. MURF FALCON TTS FUNCTION (THE MOUTH)
# ============================================================================
def generate_murf_audio(text):
    MURF_API_URL = "https://api.murf.ai/v1/speech/generate"
    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "voiceId": MURF_VOICE_ID,       
        "text": text,                    
        "modelVersion": "GEN2"            
    }
    
    try:
        response = requests.post(MURF_API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "audioFile" in data:
                audio_url = data["audioFile"]
                audio_response = requests.get(audio_url)
                if audio_response.status_code == 200:
                    return audio_response.content
            return response.content
        else:
            st.error(f"Murf API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to Murf AI: {str(e)}")
        return None

# ============================================================================
# 5. GROQ WHISPER STT FUNCTION (THE EARS)
# ============================================================================
def transcribe_voice(audio_file):
    """Converts the user's spoken audio into text using Groq Whisper."""
    try:
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        
        # The API needs a filename to know it's an audio file
        audio_file.name = "recording.wav"
        
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3", # Groq's lightning-fast Whisper model
            file=audio_file,
            response_format="text"
        )
        return transcription
    except Exception as e:
        st.error(f"Groq Transcription Error: {str(e)}")
        return None

# ============================================================================
# 6. GROQ CHAT FUNCTION (THE BRAIN)
# ============================================================================
def get_groq_response(messages):
    try:
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            max_tokens=150,  
            temperature=0.7  
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Groq API Error: {str(e)}")
        return None

# ============================================================================
# 7. USER INTERFACE
# ============================================================================
st.title("🎙️ VocalHire: AI Mock Interviewer")
st.subheader("Speak directly to the AI Hiring Manager!")
st.divider()

for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ============================================================================
# 8. START INTERVIEW BUTTON
# ============================================================================
if len(st.session_state.messages) == 1: 
    if st.button("🚀 Start Interview", type="primary"):
        with st.spinner("Interviewer is joining the room..."):
            ai_response = get_groq_response(st.session_state.messages)
            if ai_response:
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                with st.chat_message("assistant"):
                    st.write(ai_response)
                with st.spinner("🎧 Connecting to Murf Voice..."):
                    audio_bytes = generate_murf_audio(ai_response)
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/mp3", autoplay=True)

# ============================================================================
# 9. INPUT AREA (VOICE AND TEXT)
# ============================================================================
st.write("---")
st.write("**Your Turn to Answer:**")

# We capture either audio input OR text input
user_audio = st.audio_input("Click the microphone to record your answer")
user_text = st.chat_input("Or type your answer here as a backup...")

# Figure out which input the user used
final_user_input = None

if user_audio:
    with st.spinner("Transcribing your voice..."):
        final_user_input = transcribe_voice(user_audio)
elif user_text:
    final_user_input = user_text

# If we got input from either the mic or the text box, process it!
if final_user_input:
    st.session_state.messages.append({"role": "user", "content": final_user_input})
    with st.chat_message("user"):
        st.write(final_user_input)
    
    with st.spinner("🤔 Interviewer is thinking..."):
        ai_response = get_groq_response(st.session_state.messages)
    
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

# ============================================================================
# 10. SIDEBAR
# ============================================================================
with st.sidebar:
    st.header("ℹ️ About")
    st.info("VocalHire uses Groq Whisper for Voice-to-Text, Groq LLaMA for AI Logic, and Murf for Text-to-Voice.")
    
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
