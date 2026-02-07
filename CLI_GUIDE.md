# Voicebox CLI Guide

Complete guide to using the Voicebox CLI for automated audio generation from markdown scripts.

## Quick Start

```bash
# 1. Create voice profiles
python cli.py create-profile "Alex" samples/alex.wav "Hello, I'm Alex"
python cli.py create-profile "Jordan" samples/jordan.wav "Hey there, Jordan here"

# 2. Generate from template
python cli.py template podcast > my_podcast.md

# 3. Validate before generating (dry run)
python cli.py generate my_podcast.md --dry-run

# 4. Generate audio
python cli.py generate my_podcast.md --output podcast.wav
```

---

## Commands

### `generate` - Generate audio from a script

Generate audio from a markdown script file.

```bash
python cli.py generate <script.md> [options]
```

**Options:**
- `--output`, `-o` - Output file path (default: `<script_name>.wav`)
- `--model-size`, `-m` - TTS model size: `1.7B` (better quality) or `0.6B` (faster) (default: `1.7B`)
- `--format`, `-f` - Output format: `wav` or `mp3` (default: `wav`)
- `--dry-run` - Validate script without generating audio

**Examples:**
```bash
# Basic generation
python cli.py generate my_podcast.md

# Custom output path
python cli.py generate my_podcast.md --output out/episode_1.wav

# Fast model
python cli.py generate my_podcast.md --model-size 0.6B

# MP3 output (smaller file size)
python cli.py generate my_podcast.md --format mp3

# Validate before generating
python cli.py generate my_podcast.md --dry-run
```

**What happens during generation:**
1. ✓ **Pre-flight validation** - Checks profiles have samples, model is available
2. ✓ **Model loading** - Downloads/loads TTS model on first run (may take 5-10 minutes)
3. ✓ **Real-time progress** - Shows segment completion: `[3/10] 30% - Segment 3 completed`
4. ✓ **Auto-retry** - Retries failed segments up to 3 times before giving up
5. ✓ **Crossfade mixing** - Smooth transitions between segments (100ms crossfade)
6. ✓ **Format conversion** - Converts to MP3 if requested

---

### `batch` - Generate multiple scripts

Process multiple markdown scripts at once.

```bash
python cli.py batch <scripts...> [options]
```

**Options:**
- `--output-dir`, `-d` - Output directory (default: `.`)
- `--model-size`, `-m` - TTS model size (default: `1.7B`)
- `--format`, `-f` - Output format: `wav` or `mp3` (default: `wav`)
- `--dry-run` - Validate all scripts without generating

**Examples:**
```bash
# Process all markdown files in a directory
python cli.py batch scripts/*.md --output-dir out/

# Generate MP3s from multiple scripts
python cli.py batch ep1.md ep2.md ep3.md --format mp3 --output-dir podcasts/

# Validate multiple scripts
python cli.py batch scripts/*.md --dry-run
```

**Batch processing features:**
- Continues on error (won't stop if one script fails)
- Shows progress for each script: `[2/5] Processing: episode_2.md`
- Summary report at the end with success/failure counts

---

### `profiles` - List voice profiles

List all available voice profiles with sample counts.

```bash
python cli.py profiles
```

**Output:**
```
Name                      ID                                       Language   Samples
-----------------------------------------------------------------------------------------
Alex                      25ae88eb-b486-49a6-bf10-bbbc1dd56250     en         1
Jordan                    3deeedcc-42d5-4dcb-b028-08d84079606c     en         2
```

---

### `create-profile` - Create a voice profile

Create a new voice profile from an audio sample.

```bash
python cli.py create-profile <name> <sample.wav> <reference_text> [options]
```

**Options:**
- `--language`, `-l` - Language code (default: `en`)
  - Supported: `en`, `zh`, `ja`, `ko`, `de`, `fr`, `ru`, `pt`, `es`, `it`

**Examples:**
```bash
# English voice
python cli.py create-profile "Alex" samples/alex.wav "Hello, this is Alex speaking."

# Chinese voice
python cli.py create-profile "李华" samples/lihua.wav "你好，我是李华。" --language zh

# German voice
python cli.py create-profile "Hans" samples/hans.wav "Hallo, ich bin Hans." --language de
```

**Sample requirements:**
- **Duration:** 3-30 seconds (optimal: 5-10 seconds)
- **Quality:** Clear speech, minimal background noise
- **Content:** Natural speech (not singing or shouting)
- **Format:** WAV, MP3, or any format librosa supports

---

### `template` - Print markdown templates

Print a markdown template for different audio types.

```bash
python cli.py template <type>
```

**Types:**
- `podcast` - Multi-speaker conversation with sections
- `narration` - Story with narrator + character voices
- `tts` - Simple single-speaker text-to-speech

**Examples:**
```bash
# Save podcast template
python cli.py template podcast > my_podcast.md

# View narration template
python cli.py template narration

# Save TTS template
python cli.py template tts > speech.md
```

---

## Configuration File

Create a `.voicebox.json` file in your project directory to set defaults:

```json
{
  "model_size": "1.7B",
  "output_dir": "output",
  "format": "mp3",
  "crossfade_ms": 100,
  "gap_ms": 100,
  "max_retries": 2
}
```

**Available options:**
- `model_size` - Default TTS model size (`"1.7B"` or `"0.6B"`)
- `output_dir` - Default output directory for batch processing
- `format` - Default output format (`"wav"` or `"mp3"`)
- `crossfade_ms` - Crossfade duration between segments (milliseconds)
- `gap_ms` - Gap between segments (milliseconds)
- `max_retries` - Maximum retry attempts for failed segments

Command-line arguments override config file settings.

---

## Markdown Script Format

### Podcast Script

```markdown
---
title: "Episode Title"
episode: "Episode 1"
description: "Episode description"
speakers:
  host1: "Alex"
  host2: "Jordan"
---

## Introduction

host1: Welcome to the show! I'm Alex.

host2: And I'm Jordan. Today we're talking about something exciting.

## Discussion

host1: So let's dive in. What's your take on this?

host2: Great question! I think the key point is...
```

### Narration Script

```markdown
---
title: "The Story"
speakers:
  narrator: "Narrator"
  alice: "Alice"
  bob: "Bob"
---

narrator: It was a dark and stormy night.

alice: Did you hear that sound?

bob: It's just the wind.

narrator: But it wasn't just the wind...
```

### Simple TTS Script

```markdown
---
title: "Announcement"
speakers:
  speaker: "Speaker"
---

speaker: This is a simple text-to-speech announcement.

speaker: You can have multiple paragraphs.

speaker: Each line will be a separate segment.
```

**Format rules:**
- YAML frontmatter between `---` markers
- `speakers:` maps speaker IDs to display names (optional but recommended)
- Content lines: `speaker_id: Text to speak`
- Section headers (`## Title`) are ignored
- Blank lines are ignored

---

## Output Formats

### WAV (Uncompressed)
- **Quality:** Lossless, 24kHz sample rate
- **Size:** ~5 MB per minute
- **Use for:** Professional editing, mastering, archival

### MP3 (Compressed)
- **Quality:** 192 kbps (high quality)
- **Size:** ~1.4 MB per minute (70% smaller than WAV)
- **Use for:** Distribution, streaming, storage

**Note:** MP3 export requires `pydub` and `ffmpeg`:
```bash
pip install pydub
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: Download from ffmpeg.org
```

---

## Progress Monitoring

During generation, you'll see real-time progress:

```
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
  Saved: podcast.wav (12.3 MB)

Done!
```

**Progress indicators:**
- Model loading status
- Segment completion percentage
- Which segment is being generated
- Retry attempts if segments fail
- Export status and file size

---

## Error Handling

### Pre-flight Validation Errors

**Profile has no samples:**
```
Validation failed:
  Profile 'Alex' has no voice samples

Fix these issues before generating audio.
```

**Solution:** Add samples to the profile:
```bash
python cli.py create-profile "Alex" samples/alex.wav "Hello, I'm Alex"
```

### Generation Errors

**Segment fails during generation:**
```
  Segment 3 failed (attempt 1/3): Model timeout
  Retrying...
  [3/10] 30% - Segment 3 completed
```

The CLI automatically retries failed segments up to 3 times.

**Persistent failure:**
```
  Segment 5 failed after 3 attempts: CUDA out of memory

Pipeline error: CUDA out of memory
  Segment 5: CUDA out of memory
```

**Solutions:**
- Use smaller model: `--model-size 0.6B`
- Reduce GPU load by closing other applications
- Split long text into shorter segments

### MP3 Conversion Errors

**pydub not installed:**
```
  Warning: pydub not installed. Install with: pip install pydub
  Saving as WAV instead.
```

**ffmpeg not installed:**
```
  Warning: MP3 conversion failed: ffmpeg not found
  Saving as WAV instead.
```

**Solution:**
```bash
pip install pydub
# Then install ffmpeg (see Output Formats section)
```

---

## Tips & Best Practices

### Voice Profile Creation

✓ **DO:**
- Use 5-10 seconds of clear speech per sample
- Record in a quiet environment
- Use natural, conversational tone
- Add multiple samples per profile for better quality

✗ **DON'T:**
- Use music, singing, or shouting
- Use samples with background noise or echo
- Use samples shorter than 3 seconds

### Script Writing

✓ **DO:**
- Use speaker names that match profile names exactly
- Break long monologues into multiple lines
- Use section headers to organize content
- Validate with `--dry-run` before generating

✗ **DON'T:**
- Write paragraphs longer than 500 characters
- Mix languages within a single speaker turn
- Use special characters in speaker IDs

### Performance Optimization

**Fast iteration during development:**
```bash
# Use fast model for testing
python cli.py generate test.md --model-size 0.6B --dry-run
python cli.py generate test.md --model-size 0.6B
```

**Production quality:**
```bash
# Use full model for final output
python cli.py generate final.md --model-size 1.7B --format mp3
```

**Batch processing:**
```bash
# Process all episodes overnight
python cli.py batch episodes/*.md --output-dir releases/ --format mp3
```

---

## Troubleshooting

### Model Download Slow

First-time model download can take 10-30 minutes depending on internet speed.

**1.7B model:** ~3.5 GB download
**0.6B model:** ~1.2 GB download

You'll see progress during download:
```
Loading TTS model 1.7B on cuda...
Downloading: 45% [================>              ] 1.5GB/3.5GB
```

### Out of Memory Errors

**Symptoms:** `CUDA out of memory` or `RuntimeError: out of memory`

**Solutions:**
1. Use smaller model: `--model-size 0.6B`
2. Reduce batch size (process fewer scripts at once)
3. Close other GPU applications
4. Restart Python process between batches

### Audio Quality Issues

**Robotic or unnatural speech:**
- Add more voice samples to the profile (2-3 samples recommended)
- Use higher quality source audio for samples
- Try the 1.7B model instead of 0.6B

**Wrong voice used:**
- Check speaker names in script match profile names exactly
- Use `--dry-run` to verify speaker mapping before generating

**Gaps or clicks between segments:**
- Crossfade should smooth transitions automatically
- If issues persist, adjust `crossfade_ms` in `.voicebox.json`

---

## Examples

### Complete Workflow

```bash
# 1. Set up voice profiles
python cli.py create-profile "Alex" samples/alex.wav "Hello, I'm Alex"
python cli.py create-profile "Jordan" samples/jordan.wav "Hi, I'm Jordan"

# 2. Verify profiles
python cli.py profiles

# 3. Create script from template
python cli.py template podcast > episode_1.md

# 4. Edit episode_1.md with your content
# (Use Alex and Jordan as speaker names)

# 5. Validate script
python cli.py generate episode_1.md --dry-run

# 6. Generate audio
python cli.py generate episode_1.md --output releases/ep1.mp3 --format mp3

# 7. Generate entire season
python cli.py batch episodes/season1/*.md --output-dir releases/season1/ --format mp3
```

### Multi-language Podcast

```bash
# Create profiles for different languages
python cli.py create-profile "Emma" samples/emma_en.wav "Hello, I'm Emma" --language en
python cli.py create-profile "李华" samples/lihua_zh.wav "你好，我是李华" --language zh

# Note: Keep scripts monolingual - one language per script
# Create separate scripts for English and Chinese episodes
```

### Conference Talk Recording

```markdown
---
title: "Tech Conference Talk"
speakers:
  speaker: "Speaker"
  moderator: "Moderator"
---

moderator: Welcome everyone. Today we have a great talk about AI.

speaker: Thank you for having me. I'm excited to share our findings.

speaker: Let's start with the basics. Artificial intelligence has evolved...

moderator: That's fascinating. Can you elaborate on that?

speaker: Absolutely. The key insight is...
```

Generate:
```bash
python cli.py generate talk.md --output conference_talk.mp3 --format mp3
```

---

## Advanced Usage

### Custom Configuration Per Project

Create project-specific configs:

```bash
# Project A: High-quality WAV
cd project_a/
cat > .voicebox.json << EOF
{
  "model_size": "1.7B",
  "format": "wav",
  "crossfade_ms": 50
}
EOF

# Project B: Quick MP3 drafts
cd project_b/
cat > .voicebox.json << EOF
{
  "model_size": "0.6B",
  "format": "mp3",
  "max_retries": 1
}
EOF
```

### Pipeline Integration

Use in automated workflows:

```bash
#!/bin/bash
# generate_weekly_podcast.sh

# Generate this week's episode
python cli.py generate "episodes/week_$(date +%U).md" \
  --output "releases/week_$(date +%U).mp3" \
  --format mp3

# Upload to podcast host
# ... your upload script here ...
```

### Monitoring Long Runs

For very long scripts, redirect output to a log:

```bash
python cli.py generate long_script.md --output long.wav 2>&1 | tee generation.log
```

Check progress in another terminal:
```bash
tail -f generation.log
```

---

## Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `generate` | Generate audio from script | `python cli.py generate script.md` |
| `batch` | Generate from multiple scripts | `python cli.py batch *.md -d out/` |
| `profiles` | List voice profiles | `python cli.py profiles` |
| `create-profile` | Create voice profile | `python cli.py create-profile "Name" sample.wav "text"` |
| `template` | Print script template | `python cli.py template podcast` |

---

## Support

For issues, questions, or feature requests, see the main project README.
