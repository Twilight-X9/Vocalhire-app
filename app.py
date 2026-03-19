import streamlit as st
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv

# ============================================================================
# 1. CONFIGURE STREAMLIT PAGE & CSS
# ============================================================================
st.set_page_config(
    page_title = "VocalHire | AI Mock Interviewer",
    page_icon = "🎙️",
    layout = "centered",
    initial_sidebar_state = "expanded"
)

# Inject Custom CSS for Enterprise SaaS Light Mode
st.markdown("""
    < style >
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Global Typography and Colors */
html, body, [class*= "css"], .stApp {
    font - family: 'Inter', sans - serif!important;
    background - color: #F8FAFC; /* slate-50 */
}

    /* Override Streamlit's default background */
    .stApp > header {
    background - color: transparent!important;
}

/* Sidebar styling */
[data - testid="stSidebar"] {
    background - color: #ffffff;
    border - right: 1px solid #E5E7EB;
    box - shadow: 2px 0 4px rgba(0, 0, 0, 0.02);
}

[data - testid="stSidebar"] h1 {
    font - size: 1.5rem;
    font - weight: 600;
    color: #0F172A;
}

    /* Input fields and Selectboxes */
    .stTextInput input, .stSelectbox > div > div {
    border - radius: 0.5rem!important;
    border: 1px solid #E5E7EB!important;
    background - color: #ffffff!important;
    color: #0F172A!important;
    padding - left: 1rem!important;
    font - weight: 500!important;
}
    .stTextInput input: focus, .stSelectbox > div > div: focus - within {
    border - color: #2563EB!important;
    box - shadow: 0 0 0 2px rgba(37, 99, 235, 0.2)!important;
}

    /* Buttons */
    .stButton > button[kind = "primary"] {
    background - color: #2563EB!important;
    color: white!important;
    border: none!important;
    border - radius: 0.5rem!important;
    font - weight: 500!important;
    padding: 0.5rem 1rem!important;
    box - shadow: 0 1px 2px rgba(0, 0, 0, 0.05)!important;
    transition: all 0.2s ease!important;
}
    .stButton > button[kind = "primary"]:hover {
    background - color: #1D4ED8!important;
}
    
    .stButton > button[kind = "secondary"] {
    background - color: #ffffff!important;
    color: #EF4444!important;
    border: 1px solid #EF4444!important;
    border - radius: 0.5rem!important;
    font - weight: 500!important;
    transition: all 0.2s ease!important;
}
    .stButton > button[kind = "secondary"]:hover {
    background - color: #FEF2F2!important;
}

/* Audio Input overrides wrapper to look integrated */
[data - testid="stAudioInput"] {
    background - color: #ffffff;
    border - radius: 0.5rem;
    border: 1px solid #E5E7EB;
    padding: 0.5rem;
    box - shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    margin - bottom: 5rem; /* ensure space above chat input */
}

/* Chat Input */
[data - testid="stChatInput"] {
    background - color: #ffffff!important;
    border - top: 1px solid #E5E7EB!important;
    padding: 1rem 2rem!important;
}
[data - testid="stChatInput"] > div {
    border: 1px solid #E5E7EB!important;
    border - radius: 9999px!important; /* Fully rounded */
    background - color: #F8FAFC!important;
}
[data - testid="stChatInput"] input {
    color: #0F172A!important;
}

    /* Landing Card */
    .landing - card {
    background - color: #ffffff;
    border: 1px solid #E5E7EB;
    border - radius: 0.75rem;
    padding: 3rem;
    text - align: center;
    box - shadow: 0 4px 6px - 1px rgba(0, 0, 0, 0.05);
    margin - top: 2rem;
    margin - bottom: 2rem;
}
    .landing - card span.icon {
    font - size: 3rem;
}
    .landing - card h1 {
    font - size: 2.5rem;
    font - weight: 700;
    color: #0F172A;
    margin - bottom: 0.5rem;
    margin - top: 0.5rem;
}
    .landing - card p {
    font - size: 1.125rem;
    color: #64748B;
    margin - bottom: 2rem;
}

/* Hide standard UI elements */
#MainMenu { visibility: hidden; }
    header { visibility: hidden; }
    footer { visibility: hidden; }

    /* Top bar state */
    .active - top - bar {
    background - color: #ffffff;
    border: 1px solid #E5E7EB;
    border - radius: 0.5rem;
    padding: 0.75rem 1rem;
    text - align: center;
    margin - bottom: 2rem;
    color: #0F172A;
    font - weight: 600;
    box - shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    display: flex;
    align - items: center;
    justify - content: center;
    gap: 0.5rem;
}
    .status - dot {
    height: 10px;
    width: 10px;
    background - color: #16A34A; /* green-600 */
    border - radius: 50 %;
    display: inline - block;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0 % { transform: scale(0.95); box- shadow: 0 0 0 0 rgba(22, 163, 74, 0.7);
}
70 % { transform: scale(1); box- shadow: 0 0 0 6px rgba(22, 163, 74, 0); }
100 % { transform: scale(0.95); box- shadow: 0 0 0 0 rgba(22, 163, 74, 0); }
    }

    /* Scroll padding */
    .stMainBlockContainer {
    padding - bottom: 6rem;
}
</style >
    """, unsafe_allow_html=True)

# ============================================================================
# 2. SMART API KEY LOADER
# ============================================================================
load_dotenv()

def get_secret(key_name, default_val = ""):
if key_name in st.secrets:
    return st.secrets[key_name]
return os.getenv(key_name, default_val)

# Use session state for keys so they remain editable in the sidebar securely
if "GROQ_API_KEY" not in st.session_state:
st.session_state.GROQ_API_KEY = get_secret("GROQ_API_KEY")
if "MURF_API_KEY" not in st.session_state:
st.session_state.MURF_API_KEY = get_secret("MURF_API_KEY")
if "MURF_VOICE_ID" not in st.session_state:
st.session_state.MURF_VOICE_ID = get_secret("MURF_VOICE_ID", "en-US-marcus")

# ============================================================================
# 3. STATE MANAGEMENT & PROMPT
# ============================================================================
SYSTEM_PROMPT = """You are a strict but fair HR manager at a top tech company. 
Conduct a mock interview with the user.Ask one question at a time. 
Keep your questions under 2 sentences.Wait for their response."""

if "messages" not in st.session_state:
st.session_state.messages = [{ "role": "system", "content": SYSTEM_PROMPT }]

if "interview_active" not in st.session_state:
st.session_state.interview_active = False

if "latest_audio" not in st.session_state:
st.session_state.latest_audio = None

if "ai_status" not in st.session_state:
st.session_state.ai_status = "HR Manager involves..."

# ============================================================================
# 4. BACKEND FUNCTIONS
# ============================================================================
def generate_murf_audio(text):
if not st.session_state.MURF_API_KEY:
st.warning("Please configure Murf API Key in Settings.")
return None
MURF_API_URL = "https://api.murf.ai/v1/speech/generate"
headers = {
    "api-key": st.session_state.MURF_API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}
payload = {
    "voiceId": st.session_state.MURF_VOICE_ID,
    "text": text,
    "modelVersion": "GEN2"
}
try:
response = requests.post(MURF_API_URL, headers = headers, json = payload, timeout = 30)
if response.status_code == 200:
    data = response.json()
if "audioFile" in data:
    audio_url = data["audioFile"]
audio_response = requests.get(audio_url)
if audio_response.status_code == 200:
    return audio_response.content
return response.content
        else:
st.toast(f"Murf API Error: {response.status_code}", icon = "❌")
return None
    except Exception as e:
st.toast(f"Connection Error: {str(e)}", icon = "⚠️")
return None

def transcribe_voice(audio_file):
if not st.session_state.GROQ_API_KEY:
st.warning("Please configure Groq API Key in Settings.")
return None
try:
client = OpenAI(api_key = st.session_state.GROQ_API_KEY, base_url = "https://api.groq.com/openai/v1")
        # Ensure it has a valid filename extension, openai whisper requires trailing extension
audio_file.name = "recording.wav"
transcription = client.audio.transcriptions.create(
    model = "whisper-large-v3",
    file = audio_file,
    response_format = "text"
)
return transcription.text
    except Exception as e:
st.error(f"Groq Transcription Error: {str(e)}")
return None

def get_groq_response(messages):
if not st.session_state.GROQ_API_KEY:
return None
try:
client = OpenAI(api_key = st.session_state.GROQ_API_KEY, base_url = "https://api.groq.com/openai/v1")
response = client.chat.completions.create(
    model = "llama-3.1-8b-instant",
    messages = messages,
    max_tokens = 150,
    temperature = 0.7
)
return response.choices[0].message.content
    except Exception as e:
st.error(f"Groq API Error: {str(e)}")
return None

# ============================================================================
# 5. SIDEBAR(Clean Settings Menu)
# ============================================================================
with st.sidebar:
st.markdown("<h1>⚙️ Settings</h1>", unsafe_allow_html = True)
st.markdown("<p style='color: #64748B; margin-bottom: 2rem;'>Configure your interview environment</p>", unsafe_allow_html = True)

st.session_state.GROQ_API_KEY = st.text_input("Groq API Key", type = "password", value = st.session_state.GROQ_API_KEY, placeholder = "gsk_...")
st.session_state.MURF_API_KEY = st.text_input("Murf API Key", type = "password", value = st.session_state.MURF_API_KEY)

voices = {
    "Marcus (Professional Male)": "en-US-marcus",
    "Lily (Friendly Female)": "en-US-lily",
    "Clint (Deep Corporate)": "en-US-clint"
}
    
    # Pre - select matching voice or fallback
current_voice_name = next((name for name, val in voices.items() if val == st.session_state.MURF_VOICE_ID), "Marcus (Professional Male)")

selected_voice = st.selectbox("Select Voice", options = list(voices.keys()), index = list(voices.keys()).index(current_voice_name))
st.session_state.MURF_VOICE_ID = voices[selected_voice]

st.divider()

st.markdown("**Connection Status**")
groq_status = "🟢 Connected" if st.session_state.GROQ_API_KEY else "🔴 Missing"
murf_status = "🟢 Connected" if st.session_state.MURF_API_KEY else "🔴 Missing"

st.markdown(f"<p style='font-size:0.9rem'>Groq API: {groq_status}</p>", unsafe_allow_html = True)
st.markdown(f"<p style='font-size:0.9rem'>Murf API: {murf_status}</p>", unsafe_allow_html = True)

st.write("")
if st.button("End Interview & Reset", kind = "secondary", use_container_width = True):
    st.session_state.messages = [{ "role": "system", "content": SYSTEM_PROMPT }]
st.session_state.interview_active = False
st.session_state.latest_audio = None
st.rerun()

# ============================================================================
# 6. MAIN UI FLOW
# ============================================================================

if not st.session_state.interview_active:
    # -- - LANDING PAGE STATE-- -
    col1, col2, col3 = st.columns([1, 4, 1])
with col2:
st.markdown("""
    < div class= "landing-card" >
            <span class="icon">🎙️</span>
            <h1>VocalHire</h1>
            <p>Your AI Hiring Manager. Practice speaking naturally and get hired.</p>
        </div >
    """, unsafe_allow_html=True)
        
        # Center the button
        _, btn_col, _ = st.columns([1, 2, 1])
        with btn_col:
if st.button("Start Interview", type = "primary", use_container_width = True):
    st.session_state.interview_active = True

with st.spinner("HR Manager is reviewing your resume..."):

st.session_state.ai_status = "HR Manager is thinking..."
ai_response = get_groq_response(st.session_state.messages)

if ai_response:
    st.session_state.messages.append({ "role": "assistant", "content": ai_response })
st.session_state.ai_status = "HR Manager is speaking..."

audio_bytes = generate_murf_audio(ai_response)
if audio_bytes:
    st.session_state.latest_audio = audio_bytes

st.session_state.ai_status = "HR Manager is listening..."
st.rerun()

else:
    # -- - ACTIVE INTERVIEW STATE-- -
    
    # 1. Top Bar indicating status
st.markdown(f"""
    < div class= "active-top-bar" >
    <div class="status-dot"></div>
        { st.session_state.ai_status }
    </div >
    """, unsafe_allow_html=True)

    # 2. Render Chat History using HTML injection for perfect styling
    chat_html = ""
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue

if message["role"] == "user":
    chat_html += f"""
        < div style = "display: flex; justify-content: flex-end; margin-bottom: 1.5rem;" >
                <div style="background-color: #2563EB; color: #ffffff; padding: 1rem 1.25rem; border-radius: 1rem 1rem 0 1rem; max-width: 75%; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <p style="margin: 0; color: #ffffff; font-size: 1rem; line-height: 1.5;">{message['content']}</p>
                </div>
                <div style="font-size: 1.5rem; margin-left: 0.75rem; display: flex; align-items: flex-end; padding-bottom: 0.25rem;">👤</div>
            </div >
    """
        else:
chat_html += f"""
    < div style = "display: flex; justify-content: flex-start; margin-bottom: 1.5rem;" >
                <div style="font-size: 1.5rem; margin-right: 0.75rem; display: flex; align-items: flex-end; padding-bottom: 0.25rem;">💼</div>
                <div style="background-color: #F8FAFC; border: 1px solid #E5E7EB; color: #0F172A; padding: 1rem 1.25rem; border-radius: 1rem 1rem 1rem 0; max-width: 75%; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                    <p style="margin: 0; color: #0F172A; font-size: 1rem; line-height: 1.5;">{message['content']}</p>
                </div>
            </div >
    """
            
    # Output constructed HTML for chat history
    st.markdown(f'<div style="margin-bottom: 2rem;">{chat_html}</div>', unsafe_allow_html = True)

    # 3. Render Latest Audio Output
if st.session_state.latest_audio:
    st.markdown("<p style='color: #64748B; font-size: 0.8rem; text-align: center;'>🔊 Audio Playing...</p>", unsafe_allow_html = True)
st.audio(st.session_state.latest_audio, format = "audio/mp3", autoplay = True)
        # Clear once played to prevent replay loop on interactions
st.session_state.latest_audio = None

    # 4. Control Interface
    # Wrap an audio input and chat input in a neat way. 
    # Streamlit handles st.chat_input placing it at bottom natively. 
    # The st.audio_input acts as the central microphone widget.

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html = True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
user_audio = st.audio_input("Record your response")

user_text = st.chat_input("Or type your answer...")

final_user_input = None

    # Determine input source
if user_audio:
    st.session_state.ai_status = "Uploading and transcribing..."
with st.spinner("Transcribing your audio..."):
final_user_input = transcribe_voice(user_audio)
    elif user_text:
final_user_input = user_text

    # 5. Handle New Input
if final_user_input:
        # Append user message
st.session_state.messages.append({ "role": "user", "content": final_user_input })
        
        # Display thinking status immediately before fetch
st.session_state.ai_status = "HR Manager is thinking..."

with st.spinner("HR Manager is thinking..."):
ai_response = get_groq_response(st.session_state.messages)

if ai_response:
    st.session_state.messages.append({ "role": "assistant", "content": ai_response })

st.session_state.ai_status = "HR Manager is speaking..."
with st.spinner("Generating voice response..."):
audio_bytes = generate_murf_audio(ai_response)
if audio_bytes:
    st.session_state.latest_audio = audio_bytes

st.session_state.ai_status = "HR Manager is listening..."
st.rerun()
