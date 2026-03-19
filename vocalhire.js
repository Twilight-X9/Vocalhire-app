import streamlit as st
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv

# ============================================================================
# 1. CONFIGURE STREAMLIT PAGE & CSS
# ============================================================================
st.set_page_config(
    page_title="VocalHire | AI Mock Interviewer",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inject Custom CSS for a sleek, modern look
st.markdown("""
<style>
    /* Gradient text for the main title */
    .title-text {
        background: -webkit-linear-gradient(45deg, #FF4B2B, #FF416C);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3em;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0px;
    }
    .subtitle-text {
        text-align: center;
        color: #888888;
        font-size: 1.2em;
        margin-bottom: 2rem;
    }
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Style the audio player to be more subtle */
    audio {
        height: 40px;
        width: 100%;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

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
# 3. STATE MANAGEMENT & PROMPT
# ============================================================================
SYSTEM_PROMPT = """You are a strict but fair HR manager at a top tech company. 
Conduct a mock interview with the user. Ask one question at a time. 
Keep your questions under 2 sentences. Wait for their response."""

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

if "interview_active" not in st.session_state:
    st.session_state.interview_active = False

if "latest_audio" not in st.session_state:
    st.session_state.latest_audio = None

# ============================================================================
# 4. BACKEND FUNCTIONS
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
            st.toast(f"Murf API Error: {response.status_code}", icon="❌")
            return None
    except Exception as e:
        st.toast(f"Connection Error: {str(e)}", icon="⚠️")
        return None

def transcribe_voice(audio_file):
    try:
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        audio_file.name = "recording.wav"
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file,
            response_format="text"
        )
        return transcription
    except Exception as e:
        st.error(f"Groq Transcription Error: {str(e)}")
        return None

def get_groq_response(messages):
    try:
        client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=150,  
            temperature=0.7  
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Groq API Error: {str(e)}")
        return None

# ============================================================================
# 5. SIDEBAR (Clean Settings Menu)
# ============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50) # Placeholder logo
    st.title("Settings")
    
    with st.expander("🔑 API Status", expanded=True):
        st.write("✅ Groq" if GROQ_API_KEY else "❌ Groq Key Missing")
        st.write("✅ Murf" if MURF_API_KEY else "❌ Murf Key Missing")
    
    st.divider()
    st.info("VocalHire uses Groq Whisper (STT), LLaMA 3.1 (Logic), and Murf AI (TTS).")
    
    if st.button("🔄 End & Reset Interview", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.session_state.interview_active = False
        st.session_state.latest_audio = None
        st.rerun()

# ============================================================================
# 6. MAIN UI FLOW
# ============================================================================
st.markdown('<p class="title-text">VocalHire</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">Your AI Hiring Manager</p>', unsafe_allow_html=True)

# --- LANDING PAGE STATE ---
if not st.session_state.interview_active:
    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        ### Welcome to the Interview Room
        Ensure your microphone is connected. The interviewer will ask you one question at a time.
        """)
        st.write("")
        if st.button("🚀 Enter the Interview Room", type="primary", use_container_width=True):
            st.session_state.interview_active = True
            
            with st.spinner("Interviewer is reviewing your resume..."):
                ai_response = get_groq_response(st.session_state.messages)
                if ai_response:
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    audio_bytes = generate_murf_audio(ai_response)
                    if audio_bytes:
                        st.session_state.latest_audio = audio_bytes
            st.rerun()

# --- ACTIVE INTERVIEW STATE ---
else:
    # 1. Render Chat History
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "system":
                continue
            
            # Use custom avatars
            avatar = "💼" if message["role"] == "assistant" else "👤"
            with st.chat_message(message["role"], avatar=avatar):
                st.write(message["content"])

    # 2. Render Latest Audio Output (Autoplays the most recent AI response)
    if st.session_state.latest_audio:
        st.audio(st.session_state.latest_audio, format="audio/mp3", autoplay=True)
        # Clear it so it doesn't replay if the user just clicks around the page
        st.session_state.latest_audio = None 

    st.divider()

    # 3. User Input Controls (Side by Side for cleaner look)
    st.write("**Your Turn:** *Speak or type your response.*")
    
    final_user_input = None

    # Handle Text Input via st.chat_input (Anchors to bottom)
    user_text = st.chat_input("Type your answer here...")
    
    # Handle Audio Input natively inline
    user_audio = st.audio_input("Or record your voice")

    if user_audio:
        with st.spinner("Transcribing..."):
            final_user_input = transcribe_voice(user_audio)
    elif user_text:
        final_user_input = user_text

    # 4. Process User Input
    if final_user_input:
        # Append user message
        st.session_state.messages.append({"role": "user", "content": final_user_input})
        
        with st.spinner("Interviewer is thinking..."):
            ai_response = get_groq_response(st.session_state.messages)
        
        if ai_response:
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            with st.spinner("Generating voice..."):
                audio_bytes = generate_murf_audio(ai_response)
                if audio_bytes:
                    st.session_state.latest_audio = audio_bytes
        
        st.rerun()
