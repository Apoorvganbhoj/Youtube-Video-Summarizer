import re 
import os
from typing import Dict, Optional
import google.generativeai as genai
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from dotenv import load_dotenv
import os

load_dotenv()  # this loads variables from .env into os.environ
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# api_key = os.getenv("GOOGLE_API_KEY")
# if not api_key:
#     st.error("⚠️ GOOGLE_API_KEY not found in environment variables")
#     st.stop()

import langcodes
import google.generativeai as genai

# Initialize Gemini client
@st.cache_resource
def get_gemini_client():
    """Initialize and return Gemini client"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ GOOGLE_API_KEY not found in environment variables")
        st.stop()
    genai.configure(api_key=api_key)
    return genai  # return the module itself

def validate_youtube_url(url: str) -> bool:
    """Validate if the URL is a proper YouTube URL"""
    if not url:
        return False
    
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'https?://(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url.strip()):
            return True
    return False

def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL"""
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'https?://(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in youtube_patterns:
        match = re.match(pattern, url.strip())
        if match:
            return match.group(1)
    return None

def get_language_name(lang_code: str) -> str:
    """Get full language name from language code"""
    try:
        language = langcodes.Language(lang_code)
        return language.display_name()
    except:
        return lang_code

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_available_languages(video_id: str) -> Dict[str, str]:
    """Get available transcript languages for a video"""
    try:
        # Create API instance and get transcript list
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        languages = {}
        
        for transcript in transcript_list:
            lang_code = transcript.language_code
            lang_name = get_language_name(lang_code)
            languages[lang_code] = lang_name
            
        return languages
    except Exception as e:
        st.error(f"Error fetching transcript list: {str(e)}")
        return {}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_transcript(video_id: str, language_code: str) -> Optional[str]:
    """Extract transcript from YouTube video"""
    try:
        # Create API instance and get transcript
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id, languages=[language_code])
        
        # Format transcript to plain text
        formatter = TextFormatter()
        transcript_text = formatter.format_transcript(transcript_list)
        
        # Clean up the transcript
        transcript_text = transcript_text.strip()
        
        return transcript_text
    except Exception as e:
        # Try to get any available transcript if specific language fails
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.fetch(video_id)  # Get default transcript
            formatter = TextFormatter()
            transcript_text = formatter.format_transcript(transcript_list)
            return transcript_text.strip()
        except Exception as e2:
            st.error(f"Error extracting transcript: {str(e2)}")
            return None

# def generate_summary(transcript: str) -> Optional[str]:
#     """
#     Generate English summary using Gemini (preferred) or fallback models.
#     Tries GenerativeModel('gemini-1.5-flash') first if available, otherwise
#     falls back to text-bison/chat-bison via genai.generate_text.
#     """
#     if not transcript:
#         st.error("No transcript provided to summarize.")
#         return None

#     # load & validate key
#     api_key = os.getenv("GOOGLE_API_KEY")
#     if not api_key:
#         st.error("⚠️ GOOGLE_API_KEY not found in environment variables")
#         return None

#     # configure client (safe to call multiple times)
#     try:
#         genai.configure(api_key=api_key)
#     except Exception as e:
#         st.error(f"Failed to configure Gemini client: {e}")
#         return None

#     # keep prompt self-contained
#     prompt = (
#         "Please analyze the following transcript and provide a comprehensive summary in English.\n"
#         "Requirements:\n"
#         "1. Capture main topics and key points\n"
#         "2. Be structured in clear paragraphs or bullet points\n"
#         "3. Preserve logical flow\n"
#         "4. Be ~200-400 words depending on content length\n"
#         "5. Use clear, professional English\n\n"
#         "Transcript:\n\n"
#     )

#     # safety truncate if extremely long (avoid oversized payloads)
#     MAX_CHARS = 30000
#     if len(transcript) > MAX_CHARS:
#         transcript_to_send = transcript[:MAX_CHARS] + "\n\n[TRANSCRIPT TRUNCATED]"
#         st.warning("Transcript is very long — sending a truncated version to the model.")
#     else:
#         transcript_to_send = transcript

#     full_prompt = prompt + transcript_to_send

#     # 1) Try user's working approach: GenerativeModel (if installed and available)
#     try:
#         if hasattr(genai, "GenerativeModel"):
#             try:
#                 model = genai.GenerativeModel("gemini-1.5-flash")
#                 resp = model.generate_content(full_prompt)
#                 # resp.text worked for your "correct" code; handle gracefully if different shape
#                 text = getattr(resp, "text", None) or (resp.get("text") if isinstance(resp, dict) else None)
#                 if text:
#                     return text.strip()
#             except Exception as gm_err:
#                 # If error is 404, model is not available to this key/project.
#                 st.warning(f"GenerativeModel('gemini-1.5-flash') failed: {str(gm_err)}. Trying fallback models...")
#                 # continue to fallback below
#         else:
#             st.info("GenerativeModel not available in this google.generativeai package; using fallback models.")
#     except Exception as e:
#         st.warning(f"Unexpected check error for GenerativeModel: {e}. Trying fallback models...")

#     # 2) Fallback: try supported "public" model names via genai.generate_text
#     fallback_models = [
#         "models/text-bison-001",
#         "models/chat-bison-001"
#     ]
#     last_err = None
#     for fm in fallback_models:
#         try:
#             resp = genai.generate_text(
#                 model=fm,
#                 prompt=full_prompt,
#                 temperature=0.3,
#                 max_output_tokens=600
#             )
#             text = getattr(resp, "text", None) or (resp.get("text") if isinstance(resp, dict) else None)
#             if text:
#                 return text.strip()
#         except Exception as e:
#             last_err = e
#             # Provide low-verbosity warning and continue trying next fallback
#             st.warning(f"Model {fm} failed: {str(e)}")

#     # If we reach here, all attempts failed
#     if last_err:
#         # Common causes: API key lacks Generative AI API, model not enabled for project, or invalid key.
#         st.error("Failed to generate summary. Last error: " + str(last_err))
#         st.info(
#             "Common fixes:\n"
#             "- Ensure the GOOGLE_API_KEY is valid and points to a project with the Generative AI API enabled.\n"
#             "- If you want to use gemini-1.5-flash you need preview/explicit access from Google (not every project has it).\n"
#             "- Try enabling the Generative AI API in GCP console and/or use 'models/text-bison-001' which is generally available."
#         )
#     else:
#         st.error("Failed to generate summary for unknown reasons.")

#     return None

def generate_summary(transcript: str) -> Optional[str]:
    """Generate English summary using Gemini AI"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            st.error("⚠️ GOOGLE_API_KEY not found in environment variables")
            return None

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
        You are a YouTube video summarizer. Please analyze the transcript and create a well-structured English summary.
        Requirements:
        - Capture main topics and key points
        - Use clear paragraphs with logical flow
        - Around 200–400 words
        - Professional English

        Transcript:
        {transcript}
        """

        response = model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()
        else:
            return "⚠️ Unable to generate summary from the provided transcript."

    except Exception as e:
        st.error(f"Error generating summary with Gemini: {str(e)}")
        return None
