#!/usr/bin/env python3
"""
Voicebox CLI - Generate audio from markdown scripts.

Usage:
    python cli.py generate <script.md> [--output output.wav] [--model-size 1.7B]
    python cli.py profiles                          # List voice profiles
    python cli.py template <type>                   # Print a template (podcast/narration/tts)
    python cli.py create-profile <name> <sample.wav> <reference_text> [--language en]

Examples:
    # Generate a podcast from a markdown script
    python cli.py generate my_podcast.md --output podcast.wav

    # Generate with the fast model
    python cli.py generate my_podcast.md --model-size 0.6B

    # List available voice profiles
    python cli.py profiles

    # Create a voice profile from a sample
    python cli.py create-profile "Alex" samples/alex.wav "Hello, this is Alex speaking."

    # Print a podcast template
    python cli.py template podcast
"""

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent))


def load_config():
    """Load configuration from .voicebox.json if it exists."""
    config_file = Path.cwd() / ".voicebox.json"
    if config_file.exists():
        import json
        try:
            with open(config_file) as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load .voicebox.json: {e}")
    return {}


def init_backend():
    """Initialize the backend database and return a session."""
    from backend import config, database

    # Ensure data directories exist
    config.get_data_dir().mkdir(parents=True, exist_ok=True)
    database.init_db()

    # Return a direct session (not a generator)
    return database.SessionLocal()


def list_profiles(db):
    """List all voice profiles."""
    from backend.database import VoiceProfile as DBVoiceProfile, ProfileSample as DBProfileSample
    from sqlalchemy import func

    profiles = db.query(DBVoiceProfile).order_by(DBVoiceProfile.name).all()

    if not profiles:
        print("No voice profiles found.")
        print("Create one with: python cli.py create-profile <name> <sample.wav> <text>")
        return

    print(f"{'Name':<25} {'ID':<40} {'Language':<10} {'Samples':<8}")
    print("-" * 85)

    for profile in profiles:
        sample_count = db.query(func.count(DBProfileSample.id)).filter(
            DBProfileSample.profile_id == profile.id
        ).scalar()
        print(f"{profile.name:<25} {profile.id:<40} {profile.language:<10} {sample_count:<8}")


async def create_profile_cmd(db, name: str, sample_path: str, reference_text: str, language: str = "en"):
    """Create a voice profile with a sample."""
    from backend.database import VoiceProfile as DBVoiceProfile, ProfileSample as DBProfileSample
    from backend import config
    import shutil

    # Check if profile with this name already exists
    existing = db.query(DBVoiceProfile).filter_by(name=name).first()
    if existing:
        print(f"Profile '{name}' already exists (ID: {existing.id})")
        return existing

    # Validate sample file
    sample_file = Path(sample_path)
    if not sample_file.exists():
        print(f"Error: Sample file not found: {sample_path}")
        sys.exit(1)

    # Create profile
    profile_id = str(uuid.uuid4())
    profile = DBVoiceProfile(
        id=profile_id,
        name=name,
        description=f"Created via CLI",
        language=language,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(profile)

    # Copy sample to profiles directory
    profiles_dir = config.get_profiles_dir() / profile_id
    profiles_dir.mkdir(parents=True, exist_ok=True)
    dest_path = profiles_dir / f"sample{sample_file.suffix}"
    shutil.copy2(str(sample_file), str(dest_path))

    # Create sample record
    sample = DBProfileSample(
        id=str(uuid.uuid4()),
        profile_id=profile_id,
        audio_path=str(dest_path),
        reference_text=reference_text,
    )
    db.add(sample)
    db.commit()

    print(f"Created profile '{name}' (ID: {profile_id})")
    print(f"  Sample: {dest_path}")
    return profile


async def generate_audio(db, script_path: str, output_path: str, model_size: str = "1.7B", dry_run: bool = False, output_format: str = "wav"):
    """Generate audio from a markdown script file."""
    from backend.podcast import PodcastScriptParser, PodcastOrchestrator
    from backend.database import (
        PodcastProject as DBPodcastProject,
        PodcastSegment as DBPodcastSegment,
        VoiceProfile as DBVoiceProfile,
        ProfileSample as DBProfileSample,
    )
    from sqlalchemy import func
    from backend.stories import create_story, export_story_audio
    from backend.models import StoryCreate
    from backend.utils.podcast_audio import PodcastAudioMixer

    # Read script
    script_file = Path(script_path)
    if not script_file.exists():
        print(f"Error: Script file not found: {script_path}")
        sys.exit(1)

    script_content = script_file.read_text()
    print(f"Parsing script: {script_file.name}")

    # Parse
    parser = PodcastScriptParser()
    try:
        metadata, segments = parser.parse(script_content)
    except ValueError as e:
        print(f"Error parsing script: {e}")
        sys.exit(1)

    title = metadata.get("title", "Untitled")
    speakers = metadata.get("speakers", {})
    text_segments = [s for s in segments if s.get("marker_type") == "text"]

    print(f"  Title: {title}")
    print(f"  Speakers: {', '.join(speakers.keys()) if speakers else 'none defined'}")
    print(f"  Segments: {len(segments)} total ({len(text_segments)} text)")

    # Map speakers to voice profiles
    speaker_names = set()
    for seg in segments:
        if seg.get("marker_type") == "text" and seg.get("speaker"):
            speaker_names.add(seg["speaker"])

    profile_map = {}
    unmapped = []
    for speaker in speaker_names:
        # Try exact name match
        profile = db.query(DBVoiceProfile).filter_by(name=speaker).first()
        if profile:
            profile_map[speaker] = profile
            print(f"  Mapped '{speaker}' -> profile '{profile.name}' ({profile.id})")
        else:
            # Try case-insensitive match
            profile = db.query(DBVoiceProfile).filter(
                DBVoiceProfile.name.ilike(speaker)
            ).first()
            if profile:
                profile_map[speaker] = profile
                print(f"  Mapped '{speaker}' -> profile '{profile.name}' ({profile.id})")
            else:
                unmapped.append(speaker)

    if unmapped:
        print(f"\n  WARNING: No voice profiles found for speakers: {', '.join(unmapped)}")
        # Try to assign the first available profile as fallback
        fallback = db.query(DBVoiceProfile).first()
        if fallback:
            print(f"  Using fallback profile '{fallback.name}' for unmapped speakers")
            for speaker in unmapped:
                profile_map[speaker] = fallback
        else:
            print("  ERROR: No voice profiles exist. Create one first:")
            print("    python cli.py create-profile <name> <sample.wav> <reference_text>")
            sys.exit(1)

    # Create story
    story_data = StoryCreate(
        name=title,
        description=metadata.get("description") or f"Generated from {script_file.name}",
    )
    story = await create_story(story_data, db)
    print(f"\n  Created story: {story.id}")

    # Create project
    project_id = str(uuid.uuid4())
    project = DBPodcastProject(
        id=project_id,
        name=title,
        description=metadata.get("description"),
        script_content=script_content,
        metadata_json=json.dumps(metadata),
        pipeline_state="idle",
        current_segment_index=0,
        total_segments=len(segments),
        completed_count=0,
        failed_count=0,
        skipped_count=0,
        story_id=story.id,
    )
    db.add(project)

    # Create segments
    for i, segment in enumerate(segments):
        gen_settings = segment.get("generation_settings", {})
        gen_settings_json = json.dumps(gen_settings) if gen_settings else "{}"

        speaker = segment.get("speaker", "")
        profile_id = None
        if speaker in profile_map:
            profile_id = profile_map[speaker].id

        db_segment = DBPodcastSegment(
            id=segment.get("id", str(uuid.uuid4())),
            project_id=project_id,
            speaker=speaker,
            text=segment.get("text", ""),
            profile_id=profile_id,
            model_size=model_size,
            generation_settings=gen_settings_json,
            marker_type=segment.get("marker_type", "text"),
            marker_value=segment.get("marker_value"),
            segment_order=i,
            status="pending",
        )
        db.add(db_segment)

    db.commit()
    print(f"  Created project: {project_id}")

    # Pre-flight validation
    print(f"\nValidating configuration...")
    validation_errors = []

    # Check all text segments have valid profiles with samples
    for speaker, profile in profile_map.items():
        sample_count = db.query(func.count(DBProfileSample.id)).filter(
            DBProfileSample.profile_id == profile.id
        ).scalar()
        if sample_count == 0:
            validation_errors.append(f"  Profile '{profile.name}' has no voice samples")
        else:
            print(f"  ✓ Profile '{profile.name}' has {sample_count} sample(s)")

    # Check TTS model can be accessed
    try:
        from backend.tts import get_tts_model
        tts_model = get_tts_model()
        print(f"  ✓ TTS backend available ({type(tts_model).__name__})")
    except Exception as e:
        validation_errors.append(f"  TTS backend unavailable: {e}")

    if validation_errors:
        print("\n  Validation failed:")
        for err in validation_errors:
            print(err)
        print("\n  Fix these issues before generating audio.")
        sys.exit(1)

    print(f"  ✓ All validations passed")

    # Dry run mode - stop here
    if dry_run:
        print(f"\n[DRY RUN] Would generate {len(text_segments)} audio segments:")
        for i, seg in enumerate(text_segments, 1):
            speaker = seg.get("speaker")
            text_preview = seg.get("text", "")[:50] + "..." if len(seg.get("text", "")) > 50 else seg.get("text", "")
            profile_name = profile_map.get(speaker, fallback).name if speaker in profile_map or fallback else "NO PROFILE"
            print(f"  {i}. [{speaker} -> {profile_name}] {text_preview}")
        print(f"\n[DRY RUN] Output would be: {output_path}")
        print(f"[DRY RUN] Model: {model_size}")
        print(f"\nValidation successful! Remove --dry-run to generate audio.")
        return

    # Run pipeline with progress monitoring
    print(f"\nGenerating audio ({model_size} model)...")
    print(f"  Total segments: {len(text_segments)}")
    print()

    orchestrator = PodcastOrchestrator(project_id, db)

    # Poll progress during generation
    import time
    async def monitor_progress():
        """Monitor and display progress while generation runs."""
        last_completed = 0
        while True:
            await asyncio.sleep(0.5)  # Poll every 500ms

            # Reload project to get latest state
            db.expire(project)
            db.refresh(project)

            if project.completed_count > last_completed:
                completed = project.completed_count
                total = project.total_segments
                pct = (completed / total * 100) if total > 0 else 0
                print(f"  [{completed}/{total}] {pct:.0f}% - Segment {completed} completed")
                last_completed = completed

            # Check if done
            if project.pipeline_state in ["completed", "error", "paused"]:
                break

    try:
        # Start both the pipeline and the progress monitor
        pipeline_task = asyncio.create_task(orchestrator.start_pipeline())
        monitor_task = asyncio.create_task(monitor_progress())

        # Wait for pipeline to complete
        final_state = await pipeline_task

        # Cancel monitor
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

        print(f"\n  Generation complete!")
    except Exception as e:
        print(f"\n  Pipeline error: {e}")
        # Show which segments failed
        failed = db.query(DBPodcastSegment).filter_by(
            project_id=project_id, status="failed"
        ).all()
        for seg in failed:
            print(f"    Segment {seg.segment_order}: {seg.error_message}")
        sys.exit(1)

    # Export
    print(f"\nExporting audio...")
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    mixer = PodcastAudioMixer()
    metadata_with_story = dict(metadata)
    metadata_with_story["story_id"] = story.id
    audio_bytes = await mixer.assemble_podcast(project_id, metadata_with_story, db)

    if not audio_bytes:
        # Fallback: export via story system
        audio_bytes = await export_story_audio(story.id, db)

    if not audio_bytes:
        print("  Error: No audio generated")
        sys.exit(1)

    # Convert to MP3 if requested
    if output_format == "mp3":
        print(f"  Converting to MP3...")
        try:
            from pydub import AudioSegment
            import io

            # Load WAV bytes into AudioSegment
            wav_io = io.BytesIO(audio_bytes)
            audio = AudioSegment.from_wav(wav_io)

            # Export as MP3
            mp3_io = io.BytesIO()
            audio.export(mp3_io, format="mp3", bitrate="192k")
            audio_bytes = mp3_io.getvalue()

            print(f"  Converted to MP3 (192kbps)")
        except ImportError:
            print("  Warning: pydub not installed. Install with: pip install pydub")
            print("  Saving as WAV instead.")
            output_file = output_file.with_suffix('.wav')
        except Exception as e:
            print(f"  Warning: MP3 conversion failed: {e}")
            print("  Saving as WAV instead.")
            output_file = output_file.with_suffix('.wav')

    output_file.write_bytes(audio_bytes)
    size_mb = len(audio_bytes) / (1024 * 1024)
    print(f"  Saved: {output_file} ({size_mb:.1f} MB)")

    print("\nDone!")


def print_template(template_type: str):
    """Print a markdown template for the given audio type."""
    templates_dir = Path(__file__).parent / "scripts" / "templates"

    template_map = {
        "podcast": "podcast.md",
        "narration": "narration.md",
        "story": "narration.md",
        "tts": "tts.md",
    }

    if template_type not in template_map:
        print(f"Unknown template type: {template_type}")
        print(f"Available: {', '.join(template_map.keys())}")
        sys.exit(1)

    template_file = templates_dir / template_map[template_type]
    if template_file.exists():
        print(template_file.read_text())
    else:
        print(f"Template file not found: {template_file}")
        print("Run from the project root directory.")
        sys.exit(1)


def main():
    # Load config file defaults
    config = load_config()

    parser = argparse.ArgumentParser(
        description="Voicebox CLI - Generate audio from markdown scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py generate my_podcast.md --output podcast.wav
  python cli.py generate script.md --model-size 0.6B
  python cli.py profiles
  python cli.py create-profile "Alex" samples/alex.wav "Hello, this is Alex."
  python cli.py template podcast

Configuration:
  Create .voicebox.json in your project directory to set defaults.
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate audio from a markdown script")
    gen_parser.add_argument("script", help="Path to the markdown script file")
    gen_parser.add_argument("--output", "-o", default=None, help="Output file path (default: <script_name>.wav)")
    gen_parser.add_argument("--model-size", "-m", default=config.get("model_size", "1.7B"), choices=["1.7B", "0.6B"],
                           help=f"TTS model size (default: {config.get('model_size', '1.7B')})")
    gen_parser.add_argument("--format", "-f", default=config.get("format", "wav"), choices=["wav", "mp3"],
                           help=f"Output format (default: {config.get('format', 'wav')})")
    gen_parser.add_argument("--dry-run", action="store_true",
                           help="Validate script without generating audio")

    # profiles
    subparsers.add_parser("profiles", help="List available voice profiles")

    # create-profile
    cp_parser = subparsers.add_parser("create-profile", help="Create a voice profile from an audio sample")
    cp_parser.add_argument("name", help="Profile name (used as speaker name in scripts)")
    cp_parser.add_argument("sample", help="Path to a WAV audio sample (3-30 seconds)")
    cp_parser.add_argument("text", help="Transcript of the audio sample")
    cp_parser.add_argument("--language", "-l", default="en",
                          choices=["en", "zh", "ja", "ko", "de", "fr", "ru", "pt", "es", "it"],
                          help="Language code (default: en)")

    # template
    tmpl_parser = subparsers.add_parser("template", help="Print a markdown template")
    tmpl_parser.add_argument("type", choices=["podcast", "narration", "story", "tts"],
                            help="Template type")

    # batch
    batch_parser = subparsers.add_parser("batch", help="Generate audio from multiple scripts")
    batch_parser.add_argument("scripts", nargs="+", help="Paths to markdown script files (supports glob patterns)")
    batch_parser.add_argument("--output-dir", "-d", default=config.get("output_dir", "."),
                             help=f"Output directory (default: {config.get('output_dir', '.')})")
    batch_parser.add_argument("--model-size", "-m", default=config.get("model_size", "1.7B"), choices=["1.7B", "0.6B"],
                             help=f"TTS model size (default: {config.get('model_size', '1.7B')})")
    batch_parser.add_argument("--format", "-f", default=config.get("format", "wav"), choices=["wav", "mp3"],
                             help=f"Output format (default: {config.get('format', 'wav')})")
    batch_parser.add_argument("--dry-run", action="store_true",
                             help="Validate scripts without generating audio")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "template":
        print_template(args.type)
        return

    # Commands that need the backend
    db = init_backend()

    try:
        if args.command == "profiles":
            list_profiles(db)

        elif args.command == "create-profile":
            asyncio.run(create_profile_cmd(db, args.name, args.sample, args.text, args.language))

        elif args.command == "generate":
            output = args.output
            if output is None:
                # Use format from args (which may come from config)
                ext = ".mp3" if args.format == "mp3" else ".wav"
                output = Path(args.script).stem + ext
            asyncio.run(generate_audio(db, args.script, output, args.model_size, args.dry_run, args.format))

        elif args.command == "batch":
            # Expand glob patterns
            import glob
            all_scripts = []
            for pattern in args.scripts:
                matches = glob.glob(pattern)
                if matches:
                    all_scripts.extend(matches)
                else:
                    all_scripts.append(pattern)  # Keep non-matching patterns as-is

            if not all_scripts:
                print("No scripts found")
                sys.exit(1)

            print(f"Found {len(all_scripts)} script(s)")
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            success_count = 0
            failed = []

            for i, script_path in enumerate(all_scripts, 1):
                script_file = Path(script_path)
                if not script_file.exists():
                    print(f"\n[{i}/{len(all_scripts)}] Skipping {script_path} (not found)")
                    failed.append((script_path, "File not found"))
                    continue

                ext = ".mp3" if args.format == "mp3" else ".wav"
                output = output_dir / (script_file.stem + ext)

                print(f"\n{'='*60}")
                print(f"[{i}/{len(all_scripts)}] Processing: {script_file.name}")
                print(f"{'='*60}")

                try:
                    asyncio.run(generate_audio(db, str(script_file), str(output), args.model_size, args.dry_run, args.format))
                    success_count += 1
                except Exception as e:
                    print(f"\nFailed: {e}")
                    failed.append((script_path, str(e)))

            print(f"\n{'='*60}")
            print(f"Batch complete: {success_count}/{len(all_scripts)} succeeded")
            if failed:
                print(f"\nFailed scripts:")
                for script, error in failed:
                    print(f"  - {script}: {error}")
            print(f"{'='*60}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
