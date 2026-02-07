"""
Audio mixing utilities for podcast production.

Handles:
- Background music looping with fade in/out
- Sound effect insertion
- Automatic resampling to 24kHz (matching Qwen3-TTS output)
- Normalization
"""

from typing import List, Dict, Optional
import numpy as np
import librosa
import io
import soundfile as sf
from .audio import load_audio, save_audio


class PodcastAudioMixer:
    """Audio mixing with automatic resampling to target sample rate."""
    
    TARGET_SAMPLE_RATE = 24000
    
    def __init__(self, target_sample_rate: int = TARGET_SAMPLE_RATE):
        self.target_sample_rate = target_sample_rate
    
    async def assemble_podcast(self, project_id: str, metadata: Dict, db) -> bytes:
        """Assemble final podcast with resampled audio."""
        from ..database import Story as DBStory, StoryItem as DBStoryItem, Generation as DBGeneration

        # Safety check for metadata
        if metadata is None:
            metadata = {}

        # Use LEFT OUTER JOIN to include marker items with generation_id=None
        segments = db.query(DBStoryItem, DBGeneration).outerjoin(
            DBGeneration, DBStoryItem.generation_id == DBGeneration.id
        ).filter(
            DBStoryItem.story_id == metadata.get('story_id')
        ).order_by(DBStoryItem.start_time_ms).all()
        
        all_segments = self._add_intro_outro(segments, metadata, db)
        
        total_duration_ms = self._calculate_total_duration(all_segments)
        total_samples = int((total_duration_ms / 1000) * self.target_sample_rate)
        
        final_audio = np.zeros(total_samples, dtype=np.float32)
        
        current_sample = 0
        for item in all_segments:
            if item[1] is None:
                continue
            audio = self._load_audio(item[1].audio_path)
            
            trim_start = item[0].trim_start_ms or 0
            trim_end = item[0].trim_end_ms or 0
            
            trim_start_samples = int((trim_start / 1000) * self.target_sample_rate)
            trim_end_samples = int((trim_end / 1000) * self.target_sample_rate)
            
            audio = audio[trim_start_samples:len(audio) - trim_end_samples] if trim_end_samples > 0 else audio[trim_start_samples:]
            
            start_sample = int((item[0].start_time_ms / 1000) * self.target_sample_rate)
            end_sample = min(start_sample + len(audio), total_samples)

            if start_sample < total_samples and end_sample > start_sample:
                slice_end = min(end_sample, total_samples)
                # Trim audio to match slice length if needed
                slice_length = slice_end - start_sample
                audio_to_add = audio[:slice_length]
                final_audio[start_sample:slice_end] += audio_to_add
                current_sample = slice_end
        
        background_music = metadata.get('background_music') or {}
        if background_music.get('enabled'):
            final_audio = await self._mix_background_music_resampled(
                final_audio,
                background_music
            )

        sound_effects = metadata.get('sound_effects') or []
        if sound_effects:
            final_audio = self._insert_sound_effects_resampled(
                final_audio,
                sound_effects,
                all_segments
            )
        
        final_audio = self._normalize_audio(final_audio)
        
        return self._audio_to_wav_bytes(final_audio, self.target_sample_rate)
    
    def _add_intro_outro(self, segments: List, metadata: Dict, db) -> List:
        """Add intro and outro segments if configured.

        Note: Intro/outro audio must be pre-generated as segments in the pipeline.
        This method is a placeholder for future dedicated intro/outro generation.
        """
        # Return segments as-is; intro/outro are handled as regular segments
        # in the pipeline when included in the markdown script.
        return list(segments)
    
    def _calculate_total_duration(self, segments: List) -> int:
        """Calculate total duration from segments."""
        if not segments:
            return 0

        max_end_time = 0
        for story_item, generation in segments:
            if generation is None:
                continue
            end_time = story_item.start_time_ms + int(generation.duration * 1000)
            max_end_time = max(max_end_time, end_time)

        return max_end_time
    
    async def _mix_background_music_resampled(self, audio: np.ndarray, bg_config: Dict) -> np.ndarray:
        """Mix background music with automatic resampling to target sample rate."""
        
        bg_file = bg_config.get('file', '')
        if not bg_file:
            return audio
        
        try:
            bg_audio, original_sr = librosa.load(bg_file, sr=None, mono=True)
        except Exception as e:
            print(f"Warning: Failed to load background music {bg_file}: {e}")
            return audio
        
        if original_sr != self.target_sample_rate:
            bg_audio = librosa.resample(
                bg_audio,
                orig_sr=original_sr,
                target_sr=self.target_sample_rate
            )
        
        num_loops = int(np.ceil(len(audio) / len(bg_audio))) if len(bg_audio) > 0 else 1
        bg_looped = np.tile(bg_audio, num_loops)[:len(audio)]
        
        fade_in_ms = bg_config.get('fade_in', 5000)
        fade_out_ms = bg_config.get('fade_out', 10000)
        volume = bg_config.get('volume', 0.15)
        
        fade_in_samples = int((fade_in_ms / 1000) * self.target_sample_rate)
        fade_out_samples = int((fade_out_ms / 1000) * self.target_sample_rate)
        
        bg_looped[:fade_in_samples] *= np.linspace(0, 1, fade_in_samples)
        bg_looped[-fade_out_samples:] *= np.linspace(1, 0, fade_out_samples)
        
        mixed = audio + (bg_looped * volume)
        
        return mixed
    
    def _insert_sound_effects_resampled(self, audio: np.ndarray, sound_effects: Dict, segments: List) -> np.ndarray:
        """Insert sound effects with automatic resampling."""

        result_audio = audio.copy()

        for story_item, generation in segments:
            marker_type = getattr(story_item, 'marker_type', 'text')
            marker_value = getattr(story_item, 'marker_value', None)

            if marker_type == 'sound_effect' and marker_value and marker_value in sound_effects:
                sfx_file = sound_effects[marker_value]

                try:
                    sfx_audio, original_sr = librosa.load(sfx_file, sr=None, mono=True)
                except Exception as e:
                    print(f"Warning: Failed to load sound effect {sfx_file}: {e}")
                    continue

                if original_sr != self.target_sample_rate:
                    sfx_audio = librosa.resample(
                        sfx_audio,
                        orig_sr=original_sr,
                        target_sr=self.target_sample_rate
                    )

                start_sample = int((story_item.start_time_ms / 1000) * self.target_sample_rate)
                end_sample = min(start_sample + len(sfx_audio), len(result_audio))

                if start_sample < len(result_audio) and end_sample > start_sample:
                    slice_end = min(end_sample, len(result_audio))
                    result_audio[start_sample:slice_end] += sfx_audio

        return result_audio
    
    def _load_audio(self, audio_path: str) -> np.ndarray:
        """Load audio file."""
        try:
            audio, sr = librosa.load(audio_path, sr=None, mono=True)
            if sr != self.target_sample_rate:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sample_rate)
            return audio
        except Exception as e:
            print(f"Error loading audio {audio_path}: {e}")
            return np.array([])
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to prevent clipping."""
        max_val = np.abs(audio).max()
        
        if max_val > 1.0:
            audio = audio / max_val
        
        return audio
    
    def _audio_to_wav_bytes(self, audio: np.ndarray, sample_rate: int) -> bytes:
        """Convert audio array to WAV bytes."""
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format='WAV')
        buffer.seek(0)
        return buffer.read()
