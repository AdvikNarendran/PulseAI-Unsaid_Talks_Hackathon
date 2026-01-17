import streamlit as st
import os
import shutil
from streamlit_option_menu import option_menu
from dotenv import load_dotenv

# --- FFmpeg Fix for Windows (Whisper Dependency) ---
try:
    import imageio_ffmpeg
    ffmpeg_src = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dst = os.path.join(os.getcwd(), "ffmpeg.exe")
    
    # Copy if it doesn't exist or if we need to ensure it's there
    if not os.path.exists(ffmpeg_dst):
        shutil.copy(ffmpeg_src, ffmpeg_dst)
        print(f"Copied FFmpeg to: {ffmpeg_dst}")
    
    # Add current dir to PATH if not present (usually implicit, but let's be safe)
    if os.getcwd() not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + os.getcwd()
        
except Exception as e:
    print(f"Failed to setup FFmpeg: {e}")

# Import our modules
import utils
from ai_engine import AIEngine
from video_processor import process_video

# Load environment variables
load_dotenv()

# --- Page Config & Styling ---
st.set_page_config(
    page_title="PulsePoint AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Premium/Cyberpunk" Aesthetic
st.markdown("""
<style>
    /* Global Background & Text */
    .stApp {
        background-color: #0e1117;
        font-family: 'Inter', sans-serif;
    }
    .big-font {
        font-size: 24px !important;
        font-weight: 700;
        color: #00e5ff;
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
    }
    .hashtag-font {
        font-size: 16px !important;
        color: #ff0055;
        font-style: italic;
    }
    
    /* Neon Accents */
    h1, h2, h3 {
        color: #00e5ff !important;
        text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
    }
    
    /* Buttons */
    div.stButton > button {
        background: linear-gradient(45deg, #ff0055, #ff00aa); 
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 0, 85, 0.4);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 0, 85, 0.6);
        background: linear-gradient(45deg, #ff00aa, #ff0055);
    }
    
    .stSpinner > div {
        border-top-color: #00e5ff !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Main Content (v2 Dashboard) ---
# Load Config
config = utils.load_config()

# Sidebar: Configuration
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/12589/12589326.png", width=60)
    st.title("PulsePoint AI")
    st.caption("v2.1 | ByteSize Sage Hackathon")
    
    st.divider()
    
    with st.expander("ℹ️ Quick Guide"):
        st.markdown("""
        1. **Upload** video (MP4/MOV).
        2. **Set Duration** (10-60s).
        3. **Launch** Engine 🚀.
        4. **Wait** for AI (Transcription > Analysis > Rendering).
        5. **Download** clips!
        """)
    
    st.divider()
    
    with st.expander("⚙️ System Settings", expanded=False):
        api_key_val = config.get("GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
        gemini_key = st.text_input("Gemini API Key", type="password", value=api_key_val)
        
        if st.button("Save Configuration"):
            utils.save_config("GEMINI_API_KEY", gemini_key)
            st.success("Saved!")
            st.rerun()
            
    st.caption("Theme: System Default (Toggle in Streamlit Menu)")

st.title("PulsePoint AI ⚡ Dashboard")
st.markdown("### Multimodal AI Content Engine")

# Dashboard Grid
col_upload, col_preview = st.columns([1, 2])

with col_upload:
    st.markdown("#### 1. Ingest Content")
    uploaded_file = st.file_uploader("Upload Video Source (MP4)", type=["mp4", "mov"])
    if uploaded_file:
        st.video(uploaded_file) # Preview input immediately
    
    st.markdown("#### 2. Process Settings")
    
    # Defaults: fit to screen, nice UI
    st.info("Style: Fit to Screen (Letterbox)")
    
    use_subs = st.checkbox("Embed English Subtitles", value=True)
    duration = st.slider("Max Clip Duration (seconds)", 10, 60, 15)
    
    if st.button("🚀 Launch Processing Engine", use_container_width=True):
        st.session_state['processing_active'] = True
        st.session_state['current_file'] = uploaded_file

# --- Persistent Logs Logic ---
if 'log_transcription' not in st.session_state:
    st.session_state['log_transcription'] = None
if 'log_analysis' not in st.session_state:
    st.session_state['log_analysis'] = None

# Logic to run processing if active
if st.session_state.get('processing_active') and st.session_state.get('current_file'):
    uploaded_file = st.session_state['current_file'] # consistency
    
    with col_preview:
        st.markdown("#### 3. Live Operation Status")
        
        # Use Spinner for "Loading" animation
        with st.spinner("✨ AI is distilling your content... (This may take a minute)"):
            status_container = st.container(border=True)
            with status_container:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_status(msg, prog):
                    status_text.markdown(f"**Status:** {msg}")
                    progress_bar.progress(prog)

                update_status("Ingesting media...", 10)
                temp_path = utils.save_uploaded_file(uploaded_file)
                
                if temp_path:
                    try:
                        # AI Init
                        api_key = config.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
                        if not api_key:
                            st.error("API Key missing! Check Sidebar.")
                            st.session_state['processing_active'] = False # Stop
                        else:
                            engine = AIEngine(gemini_api_key=api_key)
                            
                            # Transcribe + Translate
                            update_status("Transcribing & Translating (Whisper)...", 30)
                            whisper_result = engine.transcribe_video(temp_path, task="translate")
                            transcript_segments = whisper_result['segments']
                            
                            # Save Log to State
                            st.session_state['log_transcription'] = transcript_segments
                            
                            # Analyze
                            update_status("Analyzing Semantic Content (Gemini 1.5)...", 60)
                            clips_metadata = engine.analyze_transcription_with_timestamps(transcript_segments, max_duration=duration)
                            
                            # Save Log to State
                            st.session_state['log_analysis'] = clips_metadata
                            
                            # Render
                            update_status(f"Rendering {len(clips_metadata)} Viral Clips (Letterbox Mode)...", 85)
                            
                            # Hardcoded Letterbox as requested
                            generated_paths = process_video(
                                temp_path, 
                                clips_metadata, 
                                transcript_segments=transcript_segments, 
                                use_subs=use_subs,
                                max_clip_duration=duration,
                                crop_mode="Letterbox"
                            )
                            
                            # Context
                            st.session_state['generated_clips'] = generated_paths
                            st.session_state['clips_metadata'] = clips_metadata
                            st.session_state['processing_active'] = False # Done
                            
                            update_status("Processing Complete!", 100)
                            st.balloons()
                            # Force refresh to show results safely (and show logs)
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"Processing Error: {e}")
                        utils.cleanup_temp_files([temp_path])
                        st.session_state['processing_active'] = False

# --- Render Persistent Logs (Outside Processing Loop) ---
# This ensures they stay visible even after 'processing_active' becomes False
with col_preview:
    if st.session_state.get('log_transcription'):
         with st.expander("📜 Internal Log: Raw Transcription (Persisted)", expanded=False):
            segments = st.session_state['log_transcription']
            st.write(f"**Total Segments:** {len(segments)}")
            for seg in segments[:10]:
                 st.text(f"[{seg['start']:.2f}s -> {seg['end']:.2f}s]: {seg['text']}")
            if len(segments) > 10:
                st.text("...")

    if st.session_state.get('log_analysis'):
        with st.expander("🧠 Internal Log: AI Virality Logic (Persisted)", expanded=False):
            st.json(st.session_state['log_analysis'])


# Results Grid
if 'generated_clips' in st.session_state and st.session_state['generated_clips']:
    st.divider()
    st.markdown("#### 🎬 Generated Output")
    
    # Iterate through clips
    for idx, clip_path in enumerate(st.session_state['generated_clips']):
        meta = st.session_state['clips_metadata'][idx]
        
        # Use columns for "Nice" Layout
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.video(clip_path)
            
        with c2:
            st.markdown(f'<p class="big-font">Viral Score: {meta.get("viral_score", "N/A")}/10</p>', unsafe_allow_html=True)
            st.markdown(f"**Summary:** {meta.get('summary', 'No summary')}")
            st.markdown(f'<p class="hashtag-font">{meta.get("hashtags", "")} #PulsePointAI</p>', unsafe_allow_html=True)
            
            with open(clip_path, "rb") as file:
                st.download_button(
                    label="⬇️ Download Reel",
                    data=file,
                    file_name=os.path.basename(clip_path),
                    mime="video/mp4",
                    key=f"dl_{idx}"
                )
        st.divider()
