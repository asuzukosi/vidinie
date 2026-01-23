# Vidinie - Transform articles into engaging videos

Vidinie - Transform articles into engaging videos.

## What It Does

Vidinie automatically converts PDFs into engaging video content:
- Extracts and analyzes document structure and images
- Generates natural narration scripts with AI
- Creates professional voiceover audio
- Produces videos in multiple visual styles

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up API Keys
```bash
cp env.example .env
```

Edit `.env` and add your API keys:
- `OPENAI_API_KEY` - Required for content analysis and script generation
- `ELEVENLABS_API_KEY` - Optional for high-quality voiceover (falls back to gTTS)
- `UNSPLASH_ACCESS_KEY` - Optional for stock images
- `PEXELS_API_KEY` - Optional for stock images

### 3. Generate a Video

**Interactive Terminal UI:**
```bash
python vidinie.py
```

**Command Line:**
```bash
python script.py document.pdf --style combined
```

## Video Styles

- **Combined** (Recommended): AI mixes all styles per segment for engaging variety
- **Slideshow**: Classic presentation with text overlays and images
- **Animated**: Motion graphics with dynamic effects and animations
- **AI Generated**: Custom DALL-E visuals for each segment

## Output

Videos are saved to `output/<pdf_name>_<style>.mp4`

Intermediate files (scripts, audio, images) are saved in `temp/` directory.

## Configuration

Edit `config.yaml` to customize:
- Video resolution and FPS
- Segment duration and count
- Voiceover provider and settings
- Visual style parameters

## Tech Stack

**AI Services:**
- OpenAI (GPT-5, DALL-E)
- ElevenLabs (Text-to-Speech)
- Unsplash/Pexels (Stock images)

**Python Libraries:**
- Textual - Terminal UI
- MoviePy - Video composition
- pdfplumber/PyMuPDF - PDF processing
- Pillow - Image manipulation
- gTTS - Free TTS fallback

## Project Structure

```
vidinie/
├── core/           # Pipeline modules (parsing, analysis, generation)
├── styles/         # Video style generators
├── cli/            # Terminal UI application
├── vidinie.py       # Interactive TUI entry point
├── script.py       # Command-line interface
└── config.yaml     # Configuration
```

## License

MIT License
