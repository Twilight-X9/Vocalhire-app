import streamlit as st
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv

# ============================================================================
# 1. CONFIGURE STREAMLIT PAGE
# ============================================================================
st.set_page_config(page_title="VocalHire AI", page_icon="🎙️")

st.markdown("""
<style>
    .title-text { background: -webkit-linear-gradient(45deg, #FF4B2B, #FF416C); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3em; font-weight: 800; text-align: center; margin-bottom: 0px; }
    .subtitle-text { text-align: center; color: #888888; font-size: 1.2em; margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. API KEYS & CLIENTS
# ============================================================================
load_dotenv()
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY"))
MURF_API_KEY = st.secrets.get("MURF_API_KEY", os.getenv("MURF_API_KEY"))
MURF_VOICE_ID = st.secrets.get("MURF_VOICE_ID", "en-US-marcus")

groq_client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

# ============================================================================
# 3. STATE MANAGEMENT
# ============================================================================
SYSTEM_PROMPT = "You are a professional HR interviewer. Ask one brief interview question at a time. Keep responses under 2 sentences."

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "active" not in st.session_state:
    st.session_state.active = False
if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None
if "input_key" not in st.session_state:
    st.session_state.input_key = 0 

# ============================================================================
# 4. CORE FUNCTIONS
# ============================================================================

def generate_murf_tts(text):
    url = "https://api.murf.ai/v1/speech/generate"
    headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
    payload = {"voiceId": MURF_VOICE_ID, "text": text, "modelVersion": "GEN2"}
    try:
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            audio_url = resp.json().get("audioFile")
            return requests.get(audio_url).content
    except Exception as e:
        st.error(f"Murf TTS Error: {e}")
    return None

def transcribe_audio(audio_file):
    try:
        audio_file.name = "input.wav"
        transcription = groq_client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file
        )
        return transcription.text
    except Exception as e:
        st.error(f"Groq STT Error: {e}")
        return None

def get_groq_response(messages):
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Groq LLM Error: {e}")
        return "I'm sorry, I'm having trouble thinking. Can you repeat that?"

# ============================================================================
# 5. UI LAYOUT
# ============================================================================
st.markdown('<p class="title-text">VocalHire</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">Your AI Hiring Manager</p>', unsafe_allow_html=True)

with st.sidebar:
    if st.button("Reset Interview", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.active = False
        st.session_state.audio_to_play = None
        st.rerun()

if not st.session_state.active:
    st.info("Welcome! Click below to start your mock interview.")
    if st.button("🚀 Start Interview", type="primary", use_container_width=True):
        st.session_state.active = True
        # Initial AI greeting/question
        ai_text = get_groq_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
        st.session_state.audio_to_play = generate_murf_tts(ai_text)
        st.rerun()
else:
    # Display message history
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # Play AI Voice (Autoplay enabled)
    if st.session_state.audio_to_play:
        st.audio(st.session_state.audio_to_play, format="audio/mp3", autoplay=True)
        st.session_state.audio_to_play = None 

    st.divider()

    # Conversational Input Logic
    st.write("### 🎙️ Your Turn")
    # Resetting the key forces the mic widget to clear after each response
    user_audio = st.audio_input("Record your answer", key=f"mic_{st.session_state.input_key}")

    if user_audio:
        with st.status("Processing...", expanded=False) as status:
            # 1. Transcribe Voice to Text
            status.update(label="Transcribing your voice...")
            user_text = transcribe_audio(user_audio)
            
            if user_text:
                st.session_state.messages.append({"role": "user", "content": user_text})
                
                # 2. Get Next Question from Groq
                status.update(label="Thinking of next question...")
                ai_text = get_groq_response(st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": ai_text})
                
                # 3. Generate New Speech from Murf
                status.update(label="Generating response voice...")
                st.session_state.audio_to_play = generate_murf_tts(ai_text)
                
                # Increment key to clear the microphone for the next turn
                st.session_state.input_key += 1
                status.update(label="Done!", state="complete")
                st.rerun()
