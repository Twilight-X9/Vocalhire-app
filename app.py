"""
VocalHire: AI Mock Interviewer
==============================
A Streamlit web application that conducts mock job interviews using:
- OpenAI API (GPT) for conversational logic (acting as an HR Manager)
- Murf AI Falcon TTS for generating real-time audio of the interviewer

Author: AI Developer
"""

# ============================================================================
# IMPORT LIBRARIES
# ============================================================================
import streamlit as st
from openai import OpenAI
import requests
import os
from dotenv import load_dotenv

# ============================================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================================
# Load API keys from the .env file
load_dotenv()

# Get API keys (replace these with your actual keys in the .env file)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
MURF_VOICE_ID = os.getenv("MURF_VOICE_ID", "en-US-male-john")  # Default voice

# ============================================================================
# CONFIGURE STREAMLIT PAGE
# ============================================================================
st.set_page_config(
    page_title="VocalHire: AI Mock Interviewer",
    page_icon="🎙️",  # Microphone emoji
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# SYSTEM PROMPT FOR THE HR MANAGER
# ============================================================================
# This is the initial prompt that sets up the AI's personality and behavior
SYSTEM_PROMPT = """You are a strict but fair HR manager at a top tech company. 
Conduct a mock interview with the user. Ask one question at a time. 
Keep your questions under 2 sentences. Wait for their response."""

# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================
# Store chat history across interactions
if "messages" not in st.session_state:
    # Initialize with system prompt as the first message
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# ============================================================================
# MURF FALCON TTS FUNCTION
# ============================================================================
def generate_murf_audio(text):
    """
    Generate audio from text using Murf AI's Falcon TTS model.
    
    Parameters:
        text (str): The text to convert to speech
        
    Returns:
        bytes: Audio data in MP3 format, or None if failed
    """
    # ========================================================================
    # MURF AI API CONFIGURATION
    # ========================================================================
    # Murf AI streaming endpoint for Falcon TTS model
    MURF_API_URL = "https://global.api.murf.ai/v1/speech/stream"
    
    # Prepare the request headers
    headers = {
        "api-key": MURF_API_KEY,  # Murf API key from .env
        "Content-Type": "application/json"
    }
    
    # Prepare the JSON payload for Falcon TTS
    # NOTE: Check Murf AI docs for available voices (voice_id)
    # Example voices: "Wayne", "Emily", "Jordan", "Rachel", etc.
    payload = {
        "voice_id": MURF_VOICE_ID,       # Voice ID from .env (e.g., "Wayne")
        "style": "Conversational",       # Speech style
        "text": text,                    # The text to convert to speech
        "locale": "en-US",               # Language locale
        "model": "FALCON",               # Use the Falcon TTS model (uppercase)
        "format": "MP3",                # Output format
        "sampleRate": 24000,             # Sample rate for audio
        "channelType": "MONO"           # Audio channel type
    }
    
    try:
        # Make POST request to Murf AI API with streaming
        response = requests.post(
            MURF_API_URL,
            headers=headers,
            json=payload,
            stream=True,  # Enable streaming mode
            timeout=30   # 30 second timeout
        )
        
        # Check if request was successful
        if response.status_code == 200:
            # Collect audio bytes from streaming response
            audio_chunks = []
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    audio_chunks.append(chunk)
            
            # Combine all chunks into single bytes object
            return b"".join(audio_chunks)
        else:
            # Handle API errors
            st.error(f"Murf API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        # Handle network/connection errors
        st.error(f"Network Error: {str(e)}")
        return None
    except Exception as e:
        # Handle any other unexpected errors
        st.error(f"Unexpected Error: {str(e)}")
        return None

# ============================================================================
# OPENAI CHAT FUNCTION
# ============================================================================
def get_openai_response(messages):
    """
    Get a response from OpenAI's GPT model.
    
    Parameters:
        messages (list): List of message dictionaries with 'role' and 'content'
        
    Returns:
        str: The AI's response text, or None if failed
    """
    try:
        # Initialize OpenAI client (v1.0+ syntax)
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Send request to OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use GPT-3.5 Turbo (or gpt-4 if preferred)
            messages=messages,
            max_tokens=500,  # Limit response length
            temperature=0.7  # Creativity level (0.0 = focused, 1.0 = creative)
        )
        
        # Extract and return the response content
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"OpenAI Error: {str(e)}")
        return None

# ============================================================================
# USER INTERFACE - HEADER
# ============================================================================
st.title("🎙️ VocalHire: AI Mock Interviewer")
st.subheader("Powered by Murf Falcon TTS")

# Add a divider for visual separation
st.divider()

# ============================================================================
# DISPLAY CHAT HISTORY
# ============================================================================
# Loop through all messages and display them
for message in st.session_state.messages:
    # Skip the system prompt (we don't display it in the chat)
    if message["role"] == "system":
        continue
    
    # Display each message using Streamlit's chat message component
    with st.chat_message(message["role"]):
        st.write(message["content"])

# ============================================================================
# START INTERVIEW BUTTON
# ============================================================================
# This button triggers the AI to ask the first question
if len(st.session_state.messages) == 1:  # Only system prompt exists
    if st.button("🚀 Start Interview", type="primary"):
        # Get the first question from OpenAI
        ai_response = get_openai_response(st.session_state.messages)
        
        if ai_response:
            # Add AI's response to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": ai_response
            })
            
            # Display the AI's response
            with st.chat_message("assistant"):
                st.write(ai_response)
            
            # Generate and play audio
            audio_bytes = generate_murf_audio(ai_response)
            if audio_bytes:
                st.audio(
                    audio_bytes, 
                    format="audio/mp3", 
                    autoplay=True
                )
            
            # Rerun to update the UI
            st.rerun()

# ============================================================================
# CHAT INPUT FOR USER RESPONSES
# ============================================================================
# Get user input using Streamlit's chat input component
user_input = st.chat_input("Type your answer here...")

if user_input:
    # ========================================================================
    # ADD USER'S RESPONSE TO CHAT HISTORY
    # ========================================================================
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Display user's message
    with st.chat_message("user"):
        st.write(user_input)
    
    # ========================================================================
    # GET AI'S RESPONSE
    # ========================================================================
    with st.spinner("🤔 Thinking..."):
        ai_response = get_openai_response(st.session_state.messages)
    
    if ai_response:
        # Add AI's response to chat history
        st.session_state.messages.append({
            "role": "assistant",
            "content": ai_response
        })
        
        # Display AI's response
        with st.chat_message("assistant"):
            st.write(ai_response)
        
        # ====================================================================
        # GENERATE AND PLAY AUDIO
        # ====================================================================
        with st.spinner("🎧 Generating audio..."):
            audio_bytes = generate_murf_audio(ai_response)
        
        if audio_bytes:
            # Play the audio automatically
            st.audio(
                audio_bytes, 
                format="audio/mp3", 
                autoplay=True
            )
        else:
            st.warning("Audio generation failed. Showing text only.")
        
        # Rerun to update the UI
        st.rerun()

# ============================================================================
# SIDEBAR - INFORMATION & CONTROLS
# ============================================================================
with st.sidebar:
    st.header("ℹ️ About")
    st.info("""
    **VocalHire** is an AI-powered mock interview application.
    
    It uses:
    - **OpenAI GPT** for conversational AI
    - **Murf Falcon TTS** for realistic voice output
    
    🎯 Tips:
    - Answer questions clearly and concisely
    - The AI will ask follow-up questions
    - Listen to the audio for feedback
    """)
    
    # API Key Status
    st.header("🔑 API Status")
    if OPENAI_API_KEY and OPENAI_API_KEY != "sk-your_openai_api_key_here":
        st.success("✅ OpenAI API Key: Loaded")
    else:
        st.error("❌ OpenAI API Key: Missing")
    
    if MURF_API_KEY and MURF_API_KEY != "your_murf_api_key_here":
        st.success("✅ Murf API Key: Loaded")
    else:
        st.error("❌ Murf API Key: Missing")
    
    st.write(f"**Voice ID:** {MURF_VOICE_ID}")
    
    # Reset Button
    if st.button("🔄 Reset Interview"):
        # Clear chat history but keep system prompt
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        st.rerun()

# ============================================================================
# END OF APPLICATION
# ============================================================================
