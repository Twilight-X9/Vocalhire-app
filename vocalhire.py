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
    .title-text { background: -webkit-linear-gradient(45deg, #FF4B2B, #FF416C); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3em; font-weight: 800; text-align: center; }
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
SYSTEM_PROMPT = "You are a professional HR interviewer. Ask one brief interview question at a time. Keep responses under 25 words."

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "active" not in st.session_state:
    st.session_state.active = False
if "audio_to_play" not in st.session_state:
    st.session_state.audio_to_play = None
if "input_key" not in st.session_state:
    st.session_state.input_key = 0 # Used to reset the audio widget

# ============================================================================
# 4. CORE FUNCTIONS
# ============================================================================

def generate_murf_tts(text):
    """Converts text to speech using Murf API"""
    url = "https://api.murf.ai/v1/speech/generate"
    headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
    payload = {
        "voiceId": MURF_VOICE_ID,
        "text": text,
        "modelVersion": "GEN2"
    }
    try:
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            audio_url = resp.json().get("audioFile")
            # Download the actual audio file bytes
            audio_data = requests.get(audio_url).content
            return audio_data
    except Exception as e:
        st.error(f"TTS Error: {e}")
    return None

def transcribe_audio(audio_file):
    """Transcribes user speech using Groq Whisper"""
    try:
        # Groq expects a file-like object with a name
        audio_file.name = "input.wav"
        transcription = groq_client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file
        )
        return transcription.text
    except Exception as e:
        st.error(f"STT Error: {e}")
        return None

def get_ai_logic_response():
    """Gets the next question/response from Llama 3"""
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=st.session_state.messages
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"LLM Error: {e}")
        return "Sorry, I encountered an error. Could you repeat that?"

# ============================================================================
# 5. UI LAYOUT
# ============================================================================
st.markdown('<p class="title-text">VocalHire</p>', unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    if st.button("Reset Interview"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.active = False
        st.session_state.audio_to_play = None
        st.rerun()

# Landing Page
if not st.session_state.active:
    if st.button("Start Interview", type="primary", use_container_width=True):
        st.session_state.active = True
        # Get first question immediately
        first_resp = get_ai_logic_response()
        st.session_state.messages.append({"role": "assistant", "content": first_resp})
        st.session_state.audio_to_play = generate_murf_tts(first_resp)
        st.rerun()
else:
    # Display Chat
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # Play latest AI Voice response
    if st.session_state.audio_to_play:
        st.audio(st.session_state.audio_to_play, format="audio/mp3", autoplay=True)
        st.session_state.audio_to_play = None # Clear after playing once

    st.divider()

    # User Input Area
    st.write("### 🎙️ Your Turn")
    # We use a key that changes every time to "clear" the widget
    user_audio = st.audio_input("Record your answer", key=f"audio_in_{st.session_state.input_key}")

    if user_audio:
        with st.status("Thinking...", expanded=False) as status:
            # 1. Transcribe
            st.write("Listening to you...")
            user_text = transcribe_audio(user_audio)
            
            if user_text:
                st.session_state.messages.append({"role": "user", "content": user_text})
                
                # 2. Get AI Logic
                st.write("Formulating question...")
                ai_text = get_groq_response(st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": ai_text})
                
                # 3. Generate Speech
                st.write("Synthesizing voice...")
                st.session_state.audio_to_play = generate_murf_tts(ai_text)
                
                # 4. Increment key to reset audio widget for next turn
                st.session_state.input_key += 1
                status.update(label="Response Ready!", state="complete")
                st.rerun()
