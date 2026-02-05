# Podcaster AI Automation

**Voicebox AI automation tool with podcast generation capabilities.**

This is a specialized fork of [Voicebox](https://github.com/jamiepine/voicebox) that adds comprehensive podcast production automation with AI-powered voice synthesis.

## Features

### 🎙️ Podcast Production System

- **Markdown Script Format** - Write podcast scripts in markdown with YAML frontmatter
- **Speaker Mapping** - Auto-map script speakers to voice profiles
- **Sequential Generation** - Generate segments one-by-one with error recovery
- **Progress Tracking** - Real-time SSE streaming of generation progress
- **Pipeline Control** - Start, pause, resume generation pipelines

### 🎵 Audio Mixing

- **Background Music** - Loop background music with fade in/out
- **Sound Effects** - Insert sound effects at specific timestamps
- **Automatic Resampling** - Convert all audio to 24kHz
- **Audio Normalization** - Prevent clipping in final output
- **WAV Export** - Export final podcast as high-quality WAV

### 🎤 Voice Integration

- **Voice Profile System** - Clone voices from audio samples
- **Multi-Speaker Support** - Different voices for each speaker
- **Per-Segment Configuration** - Different model sizes per segment (1.7B/0.6B)
- **Voice Prompt Caching** - Instant regeneration for same voice

### 🎛️ User Interface

- **Project Management** - Create, edit, delete podcast projects
- **Script Editor** - Real-time markdown editor with preview
- **Segment Panel** - View all parsed segments with status
- **Status Dashboard** - Track pipeline state (idle, generating, paused, completed, error)

## Quick Start

### Prerequisites

- **Backend:**
  - Python 3.11+
  - FFmpeg (for audio processing)

- **Frontend:**
  - Node.js 18+
  - Bun (package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/Tamoghna12/podcaster-ai-automation.git
cd podcaster-ai-automation

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies
bun install

# Start development servers
# Terminal 1: Backend
cd backend && python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
bun run dev
```

## Usage

### 1. Create Voice Profiles

1. Go to the **Voices** tab
2. Click **New Voice Profile**
3. Upload an audio sample (or record directly)
4. Enter reference text (what was said in the sample)
5. Click **Create Profile**

### 2. Create Podcast Project

1. Go to the **Podcasts** tab
2. Click **New Project**
3. Paste a markdown script:

```markdown
---
title: My First Podcast
speakers:
  host1: "Sarah"
  guest1: "John"
background_music:
  enabled: true
  file: "/path/to/music.mp3"
  volume: 0.15
  fade_in: 5000
  fade_out: 10000
---

host1: Welcome to our podcast! Today we're discussing AI.

guest1: It's exciting to see how AI is changing our world.

[sound_effect: applause]

host1: Thank you for tuning in! See you next time.
```

4. Click **Create**

### 3. Start Generation

1. Select your project from the list
2. Verify voice profile mappings in the segments panel
3. Click **Start** to begin generation
4. Monitor progress in real-time
5. When completed, click **Export** to download WAV file

## Script Format

### Frontmatter Metadata

```yaml
---
title: Podcast Title
episode: "Episode 1"
speakers:
  speaker_id: "Display Name"
description: Episode description

# Optional: Intro configuration
intro:
  enabled: true
  profile: "profile_id"
  text: "Welcome to the show"

# Optional: Outro configuration
outro:
  enabled: true
  profile: "profile_id"
  text: "Thanks for listening"

# Optional: Background music
background_music:
  enabled: true
  file: "/path/to/music.mp3"
  volume: 0.15
  fade_in: 5000
  fade_out: 10000

# Optional: Sound effects library
sound_effects:
  applause: "/path/to/applause.mp3"
  laugh: "/path/to/laugh.mp3"
---
```

### Content Format

```
speaker_name: Dialogue goes here

[sound_effect: effect_name]

[music_cue: cue_name]
```

## API Endpoints

### Projects

- `GET /podcast/projects` - List all projects
- `POST /podcast/projects` - Create new project
- `GET /podcast/projects/{project_id}` - Get project details
- `PUT /podcast/projects/{project_id}` - Update project
- `DELETE /podcast/projects/{project_id}` - Delete project

### Segments

- `PUT /podcast/projects/{project_id}/segments/{segment_id}` - Update segment

### Pipeline

- `POST /podcast/projects/{project_id}/start` - Start generation
- `POST /podcast/projects/{project_id}/pause` - Pause generation
- `GET /podcast/projects/{project_id}/progress` - SSE progress stream
- `POST /podcast/projects/{project_id}/export` - Export audio

## Technical Details

### Backend Architecture

- **Framework:** FastAPI
- **Database:** SQLite
- **TTS Model:** Qwen3-TTS (1.7B or 0.6B)
- **Audio Processing:** librosa, soundfile
- **Progress Streaming:** Server-Sent Events (SSE)

### Pipeline Flow

1. **Script Parsing** - Parse markdown + YAML frontmatter
2. **Segment Creation** - Create database records for each segment
3. **Story Linking** - Create linked Story for audio mixing
4. **Sequential Generation** - Generate TTS for each segment
5. **Timecoding** - Calculate sequential timecodes (300ms gaps)
6. **Audio Mixing** - Mix voices, background music, and sound effects
7. **Export** - Generate final WAV file

### Audio Specs

- **Sample Rate:** 24kHz (matching Qwen3-TTS output)
- **Format:** WAV (16-bit PCM)
- **Channels:** Mono
- **Fade Duration:** Configurable (default 5s in, 10s out)

## Development

### Project Structure

```
backend/
├── main.py              # FastAPI app with podcast endpoints
├── podcast.py           # Podcast orchestration logic
├── database.py          # Database models (PodcastProject, PodcastSegment)
├── utils/
│   └── podcast_audio.py # Audio mixing utilities
└── tts.py              # TTS model interface

app/src/
├── components/
│   └── PodcastsTab/   # Podcast UI components
├── lib/
│   ├── hooks/
│   │   └── usePodcasts.ts # Custom React hooks
│   └── api/
│       └── types.ts      # TypeScript types
└── router.tsx           # Route configuration
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend linting
cd app
bun run lint

# Type checking
bun run check
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Built on [Voicebox](https://github.com/jamiepine/voicebox) by jamiepine
- Powered by [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)
- Audio processing with [librosa](https://librosa.org/)
