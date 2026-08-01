# Akshara RSML Studio

Akshara RSML Studio is an advanced audio annotation platform designed for Rich Speech Markup Language (RSML). It is built with Streamlit and integrates a custom Wavesurfer.js component for precise, interactive audio timeline manipulation.

## Features

- **Interactive Audio Waveform**: Built with Wavesurfer.js v7, featuring smooth zooming, playback speed control, and visual region highlights.
- **Bi-directional Sync**: Clicking a text segment in the transcript automatically seeks the audio player to that exact moment, and vice-versa.
- **RSML Guidelines Compliance**: 
  - Switch instantly between **Verbatim** (exactly as spoken) and **Normalized** (clean text) views.
  - Quick access to Paralinguistic, Prosodic, and Disfluency tags.
- **Keyboard Autocomplete**: Type `@` in the editor to quickly insert standard RSML tags (e.g., `@breathe`, `@laughter`, `@stutter-block`).
- **Role-based Workflows**: Supports Annotators, Reviewers, and Admins with a robust task-queue system, feedback loops, and validation checks.

## Installation and Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/KushalManikonda/Akshara-Annotation-Platform.git
   cd Akshara-Annotation-Platform
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   ```bash
   python -m streamlit run app.py
   ```

## Development

- **Backend**: Built purely in Python using Streamlit and SQLite (via SQLAlchemy).
- **Custom Component**: The core audio player is an embedded HTML/JS component using Wavesurfer.js and Tribute.js (for `@` mentions). It communicates bidirectionally with Streamlit via the component API.

## Directory Structure

- `app.py`: Main entry point for the Streamlit application.
- `views/`: Contains the main dashboard views (Annotator, Reviewer, Admin).
- `components/`: Contains modular UI components.
  - `annotator/wavesurfer_custom/`: The custom HTML/JS Wavesurfer implementation.
- `database/`: SQLAlchemy models and SQLite setup.
- `services/`: Business logic for tasks and annotations.
- `scripts/`: Helper scripts for generating sample data and voices.

## Contributing

Please adhere to the standard RSML annotation guidelines provided when contributing to the tagging validation schema.
