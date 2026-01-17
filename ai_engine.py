import os
import google.generativeai as genai
import whisper
import json
from dotenv import load_dotenv

load_dotenv()

class AIEngine:
    def __init__(self, gemini_api_key="AIzaSyDG01gEToJPnL8x4whJ-8Ak4UREqVTzZkU"):
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
        
        # Load Whisper model (small is good balance for hackathon speed/accuracy)
        # Note: This might take a moment to download on first run
        self.whisper_model = whisper.load_model("base") 

    def transcribe_video(self, video_path, task="transcribe"):
        """Transcribes video using OpenAI Whisper. Set task='translate' for English translation."""
        try:
            # For subtitles, we might want to return segments. 
            # But the 'text' return here is for other methods.
            # We will rely on the main app calling this properly.
            result = self.whisper_model.transcribe(video_path, task=task)
            return result
        except Exception as e:
            print(f"Error in transcription: {e}")
            return None

    def _generate_with_fallback(self, prompt):
        """Tries multiple models in order of preference."""
        models = ['models/gemini-2.5-flash', 'models/gemini-2.5-pro', 'models/gemini-pro-latest', 'gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
        
        for model_name in models:
            try:
                # print(f"Trying model: {model_name}") 
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response
            except Exception as e:
                # print(f"Model {model_name} failed: {e}")
                continue
        raise Exception("All models failed.")

    def analyze_transcription_with_timestamps(self, segments, max_duration=15):
        """
        segments: list of dicts from Whisper {'start': 0.0, 'end': 1.0, 'text': '...'}
        max_duration: maximum duration of a clip in seconds
        """
        # Prepare a condensed version
        context_str = ""
        for i, seg in enumerate(segments):
            context_str += f"ID:{i} [{seg['start']:.2f}-{seg['end']:.2f}] {seg['text']}\n"
            
        prompt = f"""
        Analyze the following video transcript segments (ID, Timeout, Text) and identify 3 potential viral clips.
        
        CRITICAL CONSTRAINT: Each clip MUST be roughly 10 to {max_duration} seconds long. Do not select clips longer than {max_duration} seconds.
        
        Transcript:
        {context_str[:30000]} 
        
        Return valid JSON only:
        [
            {{
                "start_time": 10.5,
                "end_time": 25.0,
                "viral_score": 9,
                "summary": "Brief summary",
                "hashtags": "#viral #fyp"
            }}
        ]
        """
        
        try:
            response = self._generate_with_fallback(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            print(f"Error in Gemini analysis: {e}")
            # Fallback dummy data if API fails
            return [
                {"start_time": 0, "end_time": 10, "viral_score": 5, "summary": "Error in AI generation - Fallback", "hashtags": "#error"}
            ]

