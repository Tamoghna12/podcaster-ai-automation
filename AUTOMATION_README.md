# 🎙️ Voicebox Automation System

Transform markdown scripts into professional audio with AI voice cloning - now production-ready with comprehensive improvements!

## What This Is

A **fully automated podcast/audio generation system** that converts markdown scripts into high-quality audio using AI voice cloning (Qwen3-TTS). Write your script, run one command, get professional audio.

**Use cases:**
- 🎙️ **Podcasts** - Multi-speaker conversations
- 📖 **Audiobooks** - Narrated stories with character voices
- 🗣️ **TTS** - Simple text-to-speech
- 🎬 **Video voiceovers** - Automated narration
- 📻 **Radio ads** - Quick commercial generation
- 🌍 **Multi-language content** - Support for 10 languages

---

## Quick Start (5 Minutes)

```bash
# 1. Install dependencies
make setup

# 2. Create voice profiles (using your own audio samples)
python cli.py create-profile "Host" samples/host.wav "Hello, I'm your host"
python cli.py create-profile "Guest" samples/guest.wav "Hi there, I'm the guest"

# 3. Generate from template
python cli.py template podcast > my_podcast.md

# 4. Edit my_podcast.md with your content (use Host and Guest as speakers)

# 5. Validate before generating
python cli.py generate my_podcast.md --dry-run

# 6. Generate audio
python cli.py generate my_podcast.md --output podcast.mp3 --format mp3
```

**That's it!** You now have a professional podcast audio file.

---

## What Makes This Special

### 🚀 Production-Ready Features

| Feature | Description |
|---------|-------------|
| **✅ Pre-flight Validation** | Checks configuration before starting (no wasted time) |
| **✅ Real-time Progress** | See completion percentage and current segment |
| **✅ Auto-retry** | Failed segments retry automatically (up to 3 times) |
| **✅ Dry-run Mode** | Preview what will be generated without actually doing it |
| **✅ Crossfade Transitions** | Smooth audio between segments (no robotic gaps) |
| **✅ MP3 Export** | 70% smaller files vs WAV (perfect for distribution) |
| **✅ Batch Processing** | Process multiple scripts at once |
| **✅ Config Files** | Set project defaults in `.voicebox.json` |

### 🎯 Robust Error Handling

- Profile has no samples? **Clear error message**
- Model not loaded? **Auto-loads on first use**
- Network timeout? **Retries automatically**
- GPU out of memory? **Suggestions for fixes**

### 📊 Excellent UX

**Before (broken prototype):**
```
$ python cli.py generate podcast.md
TypeError: cannot unpack non-iterable dict object
```

**After (production system):**
```
$ python cli.py generate podcast.md --format mp3

Validating configuration...
  ✓ Profile 'Host' has 2 sample(s)
  ✓ Profile 'Guest' has 1 sample(s)
  ✓ TTS backend available
  ✓ All validations passed

Generating audio (1.7B model)...
  Total segments: 10

  Loading TTS model (1.7B)...
  Model loaded
  [1/10] 10% - Segment 1 completed
  [2/10] 20% - Segment 2 completed
  [3/10] 30% - Segment 3 completed
  ...
  [10/10] 100% - Segment 10 completed

  Generation complete!

Exporting audio...
  Converting to MP3...
  Saved: podcast.mp3 (8.4 MB)

Done!
```

---

## Complete Feature List

### Voice Management
- ✅ Create profiles from audio samples (3-30 seconds)
- ✅ Multiple samples per profile (better quality)
- ✅ 10 language support (EN, ZH, JA, KO, DE, FR, RU, PT, ES, IT)
- ✅ Auto-caching of voice prompts

### Script Processing
- ✅ Markdown format with YAML frontmatter
- ✅ Multi-speaker support
- ✅ Section organization
- ✅ Sound effect markers (future)
- ✅ Music cue markers (future)

### Generation Pipeline
- ✅ Automatic model downloading (first run)
- ✅ Model size selection (1.7B quality / 0.6B speed)
- ✅ Seed-based reproducibility
- ✅ Natural language instructions
- ✅ Configurable retry logic
- ✅ Per-segment progress tracking

### Audio Processing
- ✅ 24kHz output sample rate
- ✅ 100ms crossfade between segments
- ✅ Configurable gap duration
- ✅ Auto-normalization (prevent clipping)
- ✅ Multi-track support (future)

### Export Options
- ✅ WAV (lossless, 24kHz)
- ✅ MP3 (192kbps, ~70% smaller)
- ✅ Batch processing
- ✅ Custom output directories

### CLI Features
- ✅ Dry-run validation
- ✅ Real-time progress
- ✅ Config file support
- ✅ Template generation
- ✅ Batch processing
- ✅ Comprehensive error messages

---

## Documentation

| Document | Description |
|----------|-------------|
| **[CLI_GUIDE.md](CLI_GUIDE.md)** | Complete CLI reference with examples |
| **[IMPROVEMENTS.md](IMPROVEMENTS.md)** | Detailed list of all improvements made |
| **[PODCAST_README.md](PODCAST_README.md)** | Original podcast system documentation |
| **[PODCAST_SETUP_GUIDE.md](PODCAST_SETUP_GUIDE.md)** | Setup instructions for podcast features |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLI (cli.py)                         │
│  - Parsing, validation, progress monitoring             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Backend (Python FastAPI)                   │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  podcast.py │  │  profiles.py │  │  stories.py  │  │
│  │  (Pipeline) │  │  (Voices)    │  │  (Mixing)    │  │
│  └─────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  TTS Backend (backends/)                         │  │
│  │  - MLX (Apple Silicon)                           │  │
│  │  - PyTorch (CUDA/CPU)                            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼─────┐          ┌──────▼───┐
    │ Database │          │ Models   │
    │ (SQLite) │          │ (HF Hub) │
    └──────────┘          └──────────┘
```

---

## Performance

| Operation | Time (1.7B) | Time (0.6B) | Notes |
|-----------|-------------|-------------|-------|
| **Model download** | 10-30 min | 3-10 min | First time only |
| **Model load** | 30-60 sec | 10-20 sec | Per session |
| **Per segment** | 3-5 sec | 1-2 sec | ~50 words |
| **10-min podcast** | ~5 minutes | ~2 minutes | With 1.7B / 0.6B model |

**File sizes:**
- WAV: ~5 MB/minute (lossless)
- MP3: ~1.4 MB/minute (192kbps)

**Hardware recommendations:**
- **Minimum:** 8GB RAM, CPU only (slow but works)
- **Recommended:** 16GB RAM, NVIDIA GPU with 6GB+ VRAM
- **Optimal:** 32GB RAM, NVIDIA GPU with 12GB+ VRAM, Apple Silicon M1/M2

---

## Configuration

Create `.voicebox.json` in your project directory:

```json
{
  "model_size": "1.7B",
  "output_dir": "releases",
  "format": "mp3",
  "crossfade_ms": 100,
  "gap_ms": 100,
  "max_retries": 2
}
```

All settings can be overridden via command-line flags.

---

## Examples

### Basic Podcast

```bash
# Create voices
python cli.py create-profile "Alex" alex.wav "Hello, I'm Alex"
python cli.py create-profile "Jordan" jordan.wav "Hi, I'm Jordan"

# Generate
python cli.py generate podcast.md --output ep1.mp3 --format mp3
```

### Batch Production

```bash
# Generate entire season
python cli.py batch season1/*.md --output-dir releases/ --format mp3
```

### Quick Testing

```bash
# Fast model for testing
python cli.py generate test.md --model-size 0.6B --dry-run
python cli.py generate test.md --model-size 0.6B
```

### Professional Quality

```bash
# Best quality for final release
python cli.py generate final.md --model-size 1.7B --format mp3
```

---

## Workflow Examples

### Weekly Podcast Automation

```bash
#!/bin/bash
# weekly_podcast.sh

WEEK=$(date +%U)

# Generate this week's episode
python cli.py generate "scripts/week_${WEEK}.md" \
  --output "releases/week_${WEEK}.mp3" \
  --format mp3

# Upload to podcast host
# ...
```

### Multi-language Production

```bash
# Create language-specific profiles
python cli.py create-profile "Emma_EN" emma_en.wav "Hello" --language en
python cli.py create-profile "李华_ZH" lihua_zh.wav "你好" --language zh

# Generate separate episodes per language
python cli.py generate episode_en.md --output ep1_en.mp3 --format mp3
python cli.py generate episode_zh.md --output ep1_zh.mp3 --format mp3
```

### Quality Assurance Workflow

```bash
# 1. Validate all scripts
for script in scripts/*.md; do
  python cli.py generate "$script" --dry-run || echo "FAIL: $script"
done

# 2. Generate with fast model for review
python cli.py batch scripts/*.md --model-size 0.6B --output-dir drafts/

# 3. After approval, regenerate with quality model
python cli.py batch scripts/*.md --model-size 1.7B --format mp3 --output-dir releases/
```

---

## Troubleshooting

### Common Issues

**"Profile has no samples"**
```bash
python cli.py create-profile "Name" sample.wav "Sample text"
```

**"CUDA out of memory"**
```bash
# Use smaller model
python cli.py generate script.md --model-size 0.6B
```

**"pydub not installed" (for MP3 export)**
```bash
pip install pydub
brew install ffmpeg  # macOS
```

**Model download slow**
- First time downloads 3.5GB (1.7B) or 1.2GB (0.6B)
- Be patient, it only happens once
- Downloads from HuggingFace Hub

---

## Comparison with Alternatives

| Feature | Voicebox | ElevenLabs | Other TTS |
|---------|----------|------------|-----------|
| **Cost** | Free | $22-$330/mo | Varies |
| **Privacy** | Local | Cloud | Varies |
| **Customization** | Full | Limited | Limited |
| **Voice cloning** | ✅ Unlimited | ✅ Limited by plan | ❌ Usually no |
| **Multi-speaker** | ✅ Yes | ✅ Yes | ⚠️ Rare |
| **Offline** | ✅ Yes | ❌ No | ⚠️ Rare |
| **Batch processing** | ✅ Yes | ⚠️ API only | ⚠️ Rare |
| **Open source** | ✅ Yes | ❌ No | Varies |

---

## Improvements Made

### Critical Fixes (System was broken)
1. ✅ **Voice prompt return type** - Fixed tuple unpacking crash
2. ✅ **TTS model auto-load** - Fixed first-run crashes
3. ✅ **Marker items JOIN** - Fixed silently dropped sound effects

### Major Usability
4. ✅ **Real-time progress** - See what's happening during generation
5. ✅ **Pre-flight validation** - Catch errors before starting
6. ✅ **Auto-retry** - Resilient to transient failures
7. ✅ **Dry-run mode** - Preview before committing

### Enhancements
8. ✅ **Crossfade** - Smooth transitions between segments
9. ✅ **Config files** - Project-specific defaults
10. ✅ **MP3 export** - 70% smaller files
11. ✅ **Batch processing** - Process multiple scripts efficiently

**Result:** Transformed from a broken prototype into a production-ready automation system.

---

## Support & Contributing

- **Issues:** Report bugs and request features via GitHub issues
- **Docs:** Full documentation in [CLI_GUIDE.md](CLI_GUIDE.md)
- **Examples:** Sample scripts in `examples/`

---

## License

Open source - see main project LICENSE file.

---

## Credits

- **Qwen3-TTS** - AI voice synthesis model
- **Voicebox** - Desktop app and backend infrastructure
- **Improvements** - Production-ready enhancements and CLI automation

---

**Ready to automate your audio production?** Start with the [Quick Start](#quick-start-5-minutes) above!
