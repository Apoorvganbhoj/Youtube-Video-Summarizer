import streamlit as st
import os
from utils import (
    validate_youtube_url, 
    extract_video_id, 
    get_available_languages, 
    get_transcript, 
    generate_summary
)

# Configure page
st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="📹",
    layout="wide"
)

# Main title
st.title("📹 YouTube Video Summarizer")
st.markdown("Extract transcripts from YouTube videos and generate English summaries using AI")

# Sidebar for instructions
with st.sidebar:
    st.header("Instructions")
    st.markdown("""
    1. Enter a valid YouTube URL
    2. Select the video's original language
    3. Click 'Generate Summary'
    4. View the AI-generated English summary
    """)
    
    st.header("Requirements")
    st.markdown("""
    - Valid YouTube URL
    - Video must have captions/transcripts
    - Gemini API key in environment
    """)

# Main content area
col1, col2 = st.columns([2, 1])

# Initialize session state variables
if 'video_id' not in st.session_state:
    st.session_state.video_id = None
if 'selected_lang_code' not in st.session_state:
    st.session_state.selected_lang_code = None
if 'available_languages' not in st.session_state:
    st.session_state.available_languages = None

with col1:
    # URL input
    youtube_url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Enter the full YouTube URL"
    )
    
    # Validate URL when entered
    if youtube_url:
        if not validate_youtube_url(youtube_url):
            st.error("❌ Please enter a valid YouTube URL")
            st.session_state.video_id = None
        else:
            st.success("✅ Valid YouTube URL detected")
            video_id = extract_video_id(youtube_url)
            if video_id:
                st.info(f"Video ID: {video_id}")
                st.session_state.video_id = video_id
            else:
                st.error("❌ Could not extract video ID from URL")
                st.session_state.video_id = None

with col2:
    if st.session_state.video_id:
        # Language selection
        st.subheader("Language Selection")
        
        # Get available languages for the video
        with st.spinner("Fetching available languages..."):
            try:
                available_languages = get_available_languages(st.session_state.video_id)
                if available_languages:
                    st.session_state.available_languages = available_languages
                    
                    # Create language options with full names
                    language_options = {}
                    for lang_code, lang_name in available_languages.items():
                        display_name = f"{lang_name} ({lang_code})"
                        language_options[display_name] = lang_code
                    
                    selected_language = st.selectbox(
                        "Select video language:",
                        options=list(language_options.keys()),
                        help="Choose the original language of the video"
                    )
                    
                    if selected_language:
                        st.session_state.selected_lang_code = language_options[selected_language]
                        st.info(f"Selected: {st.session_state.selected_lang_code}")
                else:
                    st.error("No transcripts available for this video")
                    st.session_state.selected_lang_code = None
            except Exception as e:
                st.error(f"Error fetching languages: {str(e)}")
                st.session_state.selected_lang_code = None

# Generate summary button and results
if st.session_state.video_id and st.session_state.selected_lang_code:
    st.divider()
    
    col_btn, col_space = st.columns([1, 3])
    with col_btn:
        generate_btn = st.button(
            "🚀 Generate Summary",
            type="primary",
            use_container_width=True
        )
    
    if generate_btn:
        try:
            # Step 1: Extract transcript
            with st.spinner("Extracting transcript..."):
                transcript = get_transcript(st.session_state.video_id, st.session_state.selected_lang_code)
                if not transcript:
                    st.error("Failed to extract transcript from the video")
                    st.stop()
                
                st.success(f"✅ Transcript extracted ({len(transcript)} characters)")
            
            # Step 2: Generate summary
            with st.spinner("Generating AI summary..."):
                summary = generate_summary(transcript)
                if not summary:
                    st.error("Failed to generate summary")
                    st.stop()
            
            # Display results
            st.subheader("📄 English Summary")
            
            # Summary in a nice container
            with st.container():
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #1f77b4; color: black;">
                {summary}
                </div>
                """, unsafe_allow_html=True)
            
            # Additional info
            st.divider()
            col_info1, col_info2, col_info3 = st.columns(3)
            
            with col_info1:
                st.metric("Original Language", st.session_state.selected_lang_code)
            
            with col_info2:
                st.metric("Transcript Length", f"{len(transcript):,} chars")
            
            with col_info3:
                st.metric("Summary Length", f"{len(summary):,} chars")
            
            # Option to view full transcript
            with st.expander("📝 View Full Transcript"):
                st.text_area(
                    "Original Transcript:",
                    value=transcript,
                    height=300,
                    disabled=True
                )
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please check your inputs and try again.")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <small>Powered by Google Gemini AI | Built with Streamlit</small>
</div>
""", unsafe_allow_html=True)

