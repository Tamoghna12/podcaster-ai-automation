"""
Podcast production pipeline module.

Agentic podcast generation with:
- Markdown script parsing with frontmatter
- Voice profile auto-mapping
- Sequential generation with error recovery
- Intro/outro generation
- Background music mixing (looping)
- Sound effects insertion
- WAV export

INTEGRATION WITH STORY SYSTEM:
When a podcast project is created:
1. A Story is created automatically (linked via story_id)
2. As segments are generated, StoryItem records are created
3. Timecodes are calculated sequentially (with 300ms gaps)
4. Markers (sound effects, music cues) are handled
5. Export uses story-based mixing with metadata for BG music and SFX
"""

from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import yaml
import asyncio
import json
import uuid
from datetime import datetime
import numpy as np

from .database import (
    get_db,
    Session,
    PodcastProject as DBPodcastProject,
    PodcastSegment as DBPodcastSegment,
    Generation as DBGeneration,
    VoiceProfile as DBVoiceProfile,
    Story as DBStory,
    StoryItem as DBStoryItem
)
from .profiles import get_profile
from .history import create_generation
from .stories import (
    create_story,
    add_item_to_story,
    export_story_audio as export_story_audio_func
)
from .tts import get_tts_model
from .utils.progress import get_progress_manager
from .utils.audio import load_audio, save_audio
from .utils.podcast_audio import PodcastAudioMixer


class PipelineState(Enum):
    IDLE = "idle"
    PARSING = "parsing"
    VALIDATING = "validating"
    GENERATING = "generating"
    PAUSED_ERROR = "paused_error"
    MIXING = "mixing"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    ERROR = "error"


class PodcastScriptParser:
    """Parse markdown scripts with frontmatter metadata."""
    
    FRONTMATTER_PATTERN = r'^---\n(.*?)\n---\n(.*)$'
    SPEAKER_PATTERN = r'^([A-Za-z0-9_]+):\s*(.+)$'
    SOUND_EFFECT_PATTERN = r'\[sound_effect:\s*([^\]]+)\]'
    MUSIC_CUE_PATTERN = r'\[music_cue:\s*([^\]]+)\]'
    SECTION_PATTERN = r'^##\s+(.+)$'
    
    def parse(self, script: str) -> Tuple[dict, List[dict]]:
        """
        Parse script into metadata and segments.
        
        Returns:
            Tuple of (metadata_dict, segments_list)
        """
        # 1. Extract frontmatter
        metadata = self._parse_frontmatter(script)
        
        # 2. Parse content into segments
        segments = self._parse_content(script, metadata)
        
        # 3. Validate structure
        self._validate_segments(segments)
        
        return metadata, segments
    
    def _parse_frontmatter(self, script: str) -> dict:
        """Extract YAML frontmatter."""
        match = re.match(self.FRONTMATTER_PATTERN, script, re.MULTILINE | re.DOTALL)
        
        if not match:
            # No frontmatter, use defaults
            return {
                "title": "Untitled Podcast",
                "speakers": {},
                "intro": None,
                "outro": None,
                "background_music": None,
                "sound_effects": None
            }
        
        yaml_content = match.group(1)
        
        try:
            frontmatter_data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            print(f"Warning: Failed to parse YAML frontmatter: {e}")
            return {
                "title": "Untitled Podcast",
                "speakers": {},
                "intro": None,
                "outro": None,
                "background_music": None,
                "sound_effects": None
            }
        
        # Ensure required fields exist
        frontmatter_data.setdefault("title", "Untitled Podcast")
        frontmatter_data.setdefault("speakers", {})
        frontmatter_data.setdefault("intro", None)
        frontmatter_data.setdefault("outro", None)
        frontmatter_data.setdefault("background_music", None)
        frontmatter_data.setdefault("sound_effects", None)
        
        return frontmatter_data
    
    def _parse_content(self, script: str, metadata: dict) -> List[dict]:
        """Parse markdown content into speaker segments."""
        segments = []
        content = self._extract_content(script)
        lines = content.split('\n')
        
        current_order = 0
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and markdown headers
            if not line or re.match(self.SECTION_PATTERN, line):
                continue
            
            # Check for sound effect
            se_match = re.match(self.SOUND_EFFECT_PATTERN, line)
            if se_match:
                segments.append({
                    "id": str(uuid.uuid4()),
                    "speaker": "",
                    "text": "",
                    "order": current_order,
                    "marker_type": "sound_effect",
                    "marker_value": se_match.group(1)
                })
                current_order += 1
                continue
            
            # Check for music cue
            mc_match = re.match(self.MUSIC_CUE_PATTERN, line)
            if mc_match:
                segments.append({
                    "id": str(uuid.uuid4()),
                    "speaker": "",
                    "text": "",
                    "order": current_order,
                    "marker_type": "music_cue",
                    "marker_value": mc_match.group(1)
                })
                current_order += 1
                continue
            
            # Parse speaker turn
            speaker_match = re.match(self.SPEAKER_PATTERN, line)
            if speaker_match:
                speaker = speaker_match.group(1)
                text = speaker_match.group(2)
                
                segments.append({
                    "id": str(uuid.uuid4()),
                    "speaker": speaker,
                    "text": text,
                    "order": current_order,
                    "marker_type": "text",
                    "marker_value": None
                })
                current_order += 1
        
        return segments
    
    def _extract_content(self, script: str) -> str:
        """Remove frontmatter and return content."""
        match = re.match(self.FRONTMATTER_PATTERN, script, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(2)
        return script
    
    def _validate_segments(self, segments: List[dict]):
        """Validate segments structure."""
        if not segments:
            raise ValueError("No segments found in script")


class PodcastOrchestrator:
    """Agentic podcast generation orchestrator with database persistence."""
    
    def __init__(self, project_id: str, db: Session):
        self.project_id = project_id
        self.db = db
        self.progress_manager = get_progress_manager()
        
        # Load project from database
        self.project = db.query(DBPodcastProject).filter_by(id=project_id).first()
        if not self.project:
            raise ValueError(f"Podcast project {project_id} not found")
        
        # Load segments from database
        self.segments = db.query(DBPodcastSegment).filter_by(
            project_id=project_id
        ).order_by(DBPodcastSegment.segment_order).all()
        
        # Parse metadata from JSON
        try:
            self.metadata = json.loads(self.project.metadata_json)
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse metadata JSON: {e}")
            self.metadata = {
                "title": self.project.name,
                "speakers": {},
                "intro": None,
                "outro": None,
                "background_music": None,
                "sound_effects": None
            }
        
        # Initialize mixer
        self.mixer = PodcastAudioMixer()
    
    async def start_pipeline(self) -> str:
        """Start or resume pipeline."""
        # Update state to generating
        self.project.pipeline_state = "generating"
        if self.project.started_at is None:
            self.project.started_at = datetime.utcnow()
        self.db.commit()
        
        try:
            # Generate from current segment index (resume if stopped)
            for i in range(self.project.current_segment_index, len(self.segments)):
                segment = self.segments[i]
                
                # Check if already completed
                if segment.status == "completed":
                    self.project.current_segment_index = i + 1
                    self.db.commit()
                    continue
                
                # Generate segment
                await self._generate_segment(segment)
                
                # Update progress
                self.project.current_segment_index = i + 1
                self._update_progress()
                self.db.commit()
            
            # All segments complete - update story item timecodes
            if self.project.story_id:
                await self._update_story_timecodes()
            
            # All segments complete
            await self._mix_and_export()
            
            # Mark as completed
            self.project.pipeline_state = "completed"
            self.project.completed_at = datetime.utcnow()
            self.db.commit()
            
            return "completed"
        
        except Exception as e:
            # Mark as error
            self.project.pipeline_state = "error"
            self.db.commit()
            raise
    
    async def _generate_segment(self, segment: DBPodcastSegment):
        """Generate audio for single segment with persistence."""
        
        # Skip non-text segments
        if segment.marker_type != "text":
            segment.status = "completed"
            self.db.commit()
            return
        
        # Update segment status
        segment.status = "generating"
        segment.error_message = None
        self.db.commit()
        
        # Update progress
        self._update_progress()
        
        try:
            # Parse generation settings
            gen_settings = json.loads(segment.generation_settings) if segment.generation_settings else {}
            
            # Get model size from segment (per-segment configuration)
            model_size = segment.model_size or "1.7B"
            
            # Load model if different size
            tts_model = get_tts_model()
            if hasattr(tts_model, '_current_model_size') and tts_model._current_model_size != model_size:
                await tts_model.load_model_async(model_size)
            
            # Get voice prompt
            voice_prompt = await self._get_voice_prompt(segment.profile_id)
            
            # Generate with configurable parameters
            audio, sample_rate = await tts_model.generate(
                text=segment.text,
                voice_prompt=voice_prompt,
                language="en",
                seed=None,
                instruct=gen_settings.get('instruct')
            )
            
            # Save generation to database
            generation = await create_generation(
                profile_id=segment.profile_id,
                text=segment.text,
                language="en",
                model_size=model_size,
                audio_path="",  # Will be set by save_audio
                duration=len(audio) / sample_rate,
                instruct=gen_settings.get('instruct'),
                db=self.db
            )
            
            # Save audio file
            from . import config
            generations_dir = config.get_generations_dir()
            audio_filename = f"{generation.id}.wav"
            audio_path = str(generations_dir / audio_filename)
            save_audio(audio, audio_path, sample_rate)
            
            # Update generation with audio path
            generation.audio_path = audio_path
            self.db.commit()
            
            # Link segment to generation
            segment.generation_id = generation.id
            segment.status = "completed"
            
            # Create story item for this segment
            if self.project.story_id:
                from .database import StoryItem as DBStoryItem
                story_item = DBStoryItem(
                    id=str(uuid.uuid4()),
                    story_id=self.project.story_id,
                    generation_id=generation.id,
                    start_time_ms=0,  # Will be updated later
                    trim_start_ms=0,
                    trim_end_ms=0,
                    volume=1.0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                self.db.add(story_item)
            
            # Create story items for markers (sound effects, music cues)
            if self.project.story_id:
                await self._create_marker_story_items()
            
            # Update project stats
            self.project.completed_count += 1
            self.db.commit()
        
        except Exception as e:
            # Mark segment as failed
            segment.status = "failed"
            segment.error_message = str(e)
            self.project.failed_count += 1
            self.db.commit()
            
            # Pause pipeline
            self.project.pipeline_state = "paused"
            self.db.commit()
            
            raise
    
    async def _get_voice_prompt(self, profile_id: Optional[str]) -> dict:
        """Get voice prompt for profile."""
        if not profile_id:
            return {}
        
        # Import here to avoid circular dependency
        from .profiles import create_voice_prompt_for_profile
        voice_prompt, _ = await create_voice_prompt_for_profile(
            profile_id=profile_id,
            db=self.db,
            use_cache=True
        )
        return voice_prompt
    
    async def resume_from_segment(self, segment_index: int):
        """Resume pipeline from specific segment (skip failed ones)."""
        
        # Mark all segments before index as skipped
        for i in range(0, segment_index):
            segment = self.segments[i]
            if segment.status == "pending":
                segment.status = "skipped"
                self.project.skipped_count += 1
        
        # Update project state
        self.project.current_segment_index = segment_index
        self.project.pipeline_state = "generating"
        self.db.commit()
        
        # Resume pipeline
        return await self.start_pipeline()
    
    def _update_progress(self):
        """Update progress for SSE streaming."""
        total = len(self.segments)
        completed = self.project.completed_count
        
        if total > 0:
            percentage = (completed / total) * 100
        else:
            percentage = 0.0
        
        self.progress_manager.update_progress(
            model_name=f"podcast-{self.project_id}",
            current=completed,
            total=total,
            filename=f"Segment {self.project.current_segment_index + 1}/{total}",
            status=self.project.pipeline_state
        )
    
    async def _update_story_timecodes(self):
        """Update story items with sequential timecodes based on segment order."""
        from .database import StoryItem as DBStoryItem, Generation as DBGeneration
        
        # Get all segments (text and markers) in order
        all_segments = self.db.query(DBPodcastSegment).filter(
            DBPodcastSegment.project_id == self.project_id,
            DBPodcastSegment.status.in_(["completed", "skipped"])
        ).order_by(DBPodcastSegment.segment_order).all()
        
        # Calculate sequential timecodes
        current_time_ms = 0
        gap_between_segments = 300  # 300ms gap between segments
        
        for segment in all_segments:
            if segment.marker_type == "text" and segment.generation_id:
                # Get the generation for text segments
                generation = self.db.query(DBGeneration).filter_by(
                    id=segment.generation_id
                ).first()
                
                if generation:
                    # Find the story item for this generation
                    story_item = self.db.query(DBStoryItem).filter_by(
                        story_id=self.project.story_id,
                        generation_id=generation.id
                    ).first()
                    
                    if story_item:
                        # Set the start time
                        story_item.start_time_ms = current_time_ms
                        
                        # Calculate next start time (add duration + gap)
                        segment_duration_ms = int(generation.duration * 1000)
                        current_time_ms += segment_duration_ms + gap_between_segments
                        
                        self.db.commit()
            
            elif segment.marker_type in ["sound_effect", "music_cue"]:
                # For markers, we might want to place them at specific positions
                # For now, just continue with current time
                # The mixer will handle inserting the effects at the appropriate positions
                pass
    
    async def _create_marker_story_items(self):
        """Create story items for markers (sound effects, music cues)."""
        from .database import StoryItem as DBStoryItem
        
        # Get all marker segments that haven't been processed yet
        marker_segments = self.db.query(DBPodcastSegment).filter(
            DBPodcastSegment.project_id == self.project_id,
            DBPodcastSegment.marker_type.in_(["sound_effect", "music_cue"]),
            DBPodcastSegment.generation_id == None  # Not yet processed
        ).order_by(DBPodcastSegment.segment_order).all()
        
        for segment in marker_segments:
            # Create a placeholder story item for the marker
            # The actual audio will be mixed by the mixer based on metadata
            story_item = DBStoryItem(
                id=str(uuid.uuid4()),
                story_id=self.project.story_id,
                generation_id=None,  # Markers don't have generations
                start_time_ms=0,  # Will be calculated in _update_story_timecodes
                trim_start_ms=0,
                trim_end_ms=0,
                volume=1.0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self.db.add(story_item)
            self.db.commit()
    
    async def _mix_and_export(self):
        """Mix all segments and export final audio."""
        
        # Export story audio (includes voice segments, music, effects)
        if self.project.story_id:
            audio_bytes = await export_story_audio_func(
                story_id=self.project.story_id,
                db=self.db
            )
        else:
            # Fallback: no story created
            print("Warning: No story associated with podcast project")
            audio_bytes = None
        
        # This will be exported via /export endpoint
        return audio_bytes


# Global orchestrator instances (for multi-project support)
_active_orchestrators: Dict[str, PodcastOrchestrator] = {}


def get_orchestrator(project_id: str, db: Session) -> PodcastOrchestrator:
    """Get or create orchestrator instance."""
    global _active_orchestrators
    
    if project_id not in _active_orchestrators:
        _active_orchestrators[project_id] = PodcastOrchestrator(project_id, db)
    
    return _active_orchestrators[project_id]


def reset_orchestrators():
    """Reset all orchestrator instances (useful for testing)."""
    global _active_orchestrators
    _active_orchestrators = {}
