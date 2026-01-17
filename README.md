# PulsePoint AI ⚡
### *A ByteSize Sage Hackathon Project*

**PulsePoint AI** is a tool I built to help creators and students turn long videos (like Zoom recordings, podcasts, or lectures) into short, shareable clips automatically.

I used **Google Gemini** to understand the video content and **OpenAI Whisper** for transcription, so it knows exactly which parts are interesting enough to be a "Reel" or "TikTok".

---

## 📸 Demo

[![Demo Video]((https://drive.google.com/file/d/1uD9mHcUZJs-Fyq6UIaMaB_9QF1b-KjvP/view?usp=sharing)D)]

---

## ✨ Features

*   ** Finds the Best Moments:** Uses Gemini 2.5 Flash to read the transcript and find funny or important parts.
*   ** Auto-Subtitles:** I matched the subtitles to the exact words spoken (Speech-to-Text).
*   ** Vertical Video:** Automatically centers the video and adds black bars (Letterbox) so it fits on phone screens.
*   ** Viral Score:** The AI rates how "viral" a clip might be from 1-10.
*   ** Hashtags:** Generates tags automatically.

## 🛠️ Built With

*   **Python** (Logic)
*   **Streamlit** (Frontend/UI)
*   **Google Gemini 2.5 Flash** (AI Model)
*   **OpenAI Whisper** (Transcription)
*   **MoviePy** (Video Editing)

---

## 🚀 How to Run It

1.  **Clone the repo**
    ```bash
    git clone https://github.com/your-username/pulsepoint-ai.git
    cd pulsepoint-ai
    ```

2.  **Install the requirements**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the app**
    ```bash
    streamlit run app.py
    ```

4.  **Add your API Key**: On the sidebar, paste your **Google Gemini API Key** and click Save.

---

## 📂 Project Structure
Here's what each file does:

*   **`app.py`**: The main Ibsite code (Streamlit). It handles the upload, the slider, and shows the progress bars.
*   **`ai_engine.py`**: Talk to the AI. It sends the video transcript to Gemini to find the best clips and uses Whisper to convert speech to text.
*   **`video_processor.py`**: The video editor. It cuts the video, makes it vertical (9:16), and burns the subtitles onto the video.
*   **`utils.py`**: Helper functions (like saving files and loading API keys).

---

## �‍💻 Team
Built for the **UnsaidTalks "ByteSize Sage" Hackathon**.
I wanted to see if I could make video editing easier with AI!
