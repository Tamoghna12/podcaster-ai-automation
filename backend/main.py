"""
FastAPI application for voicebox backend.

Handles voice cloning, generation history, and server mode.
Focused on Linux + Nvidia GPU compatibility.
"""

from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime
import asyncio
import uvicorn
import argparse
import tempfile
import io
from pathlib import Path
import uuid
import os

from . import database, models, profiles, history, tts, config, export_import, channels, stories, __version__
from .database import get_db, Generation as DBGeneration, VoiceProfile as DBVoiceProfile
from .database import PodcastProject as DBPodcastProject, PodcastSegment as DBPodcastSegment
from .utils.progress import get_progress_manager
from .utils.tasks import get_task_manager
from .utils.cache import clear_voice_prompt_cache
from .platform_detect import get_backend_type

app = FastAPI(
    title="voicebox API",
    description="Production-quality Qwen3-TTS voice cloning API",
    version=__version__,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# ROOT & HEALTH ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "voicebox API", "version": __version__}


@app.post("/shutdown")
async def shutdown():
    """Gracefully shutdown server."""
    async def shutdown_async():
        await asyncio.sleep(0.1)
        os.kill(os.getpid(), 9)

    asyncio.create_task(shutdown_async())
    return {"message": "Shutting down..."}


@app.get("/health", response_model=models.HealthResponse)
async def health():
    """Health check endpoint - Linux + Nvidia GPU compatible."""
    
    backend_type = get_backend_type()
    
    has_cuda = False
    gpu_type = None
    gpu_memory = None
    
    try:
        import torch
        has_cuda = torch.cuda.is_available()
        
        if has_cuda:
            gpu_type = f"CUDA ({torch.cuda.get_device_name(0)})"
            gpu_memory = {
                "allocated_gb": torch.cuda.memory_allocated() / 1024**3,
                "reserved_gb": torch.cuda.memory_reserved() / 1024**3,
                "max_allocated_gb": torch.cuda.max_memory_allocated() / 1024**3,
            }
        else:
            gpu_type = "CPU only (no CUDA)"
    except ImportError:
        gpu_type = "torch not installed"
    except Exception as e:
        gpu_type = f"GPU detection error: {str(e)}"
    
    model_loaded = False
    model_size = None
    try:
        tts_model = tts.get_tts_model()
        model_size = getattr(tts_model, '_current_model_size', None)
        if not model_size:
            model_size = getattr(tts_model, 'model_size', None)
        model_loaded = model_size is not None
    except Exception:
        model_loaded = False
    
    vram_used_mb_val = None
    if has_cuda and isinstance(gpu_memory, dict):
        vram_used_mb_val = gpu_memory.get('allocated_gb', 0.0) * 1024

    return models.HealthResponse(
        status="ok",
        model_loaded=model_loaded,
        model_downloaded=None,
        model_size=model_size,
        gpu_available=has_cuda,
        gpu_type=gpu_type,
        vram_used_mb=vram_used_mb_val,
        backend_type=backend_type,
    )


# ============================================
# SERVER MODES
# ============================================

@app.get("/server/mode")
async def get_server_mode():
    """Get current server mode."""
    import socket
    hostname = socket.gethostname()
    return {
        "mode": "local",
        "hostname": hostname,
        "port": 17493,
        "platform": "linux",
    }


# ============================================
# PODCAST PRODUCTION ENDPOINTS
# ============================================

from . import podcast


@app.get("/podcast/projects")
async def list_podcast_projects(db: Session = Depends(get_db)):
    """List all podcast projects."""
    projects = db.query(DBPodcastProject).order_by(
        DBPodcastProject.updated_at.desc()
    ).all()
    
    result = []
    for project in projects:
        try:
            import json
            metadata_dict = json.loads(project.metadata_json)
        except (json.JSONDecodeError, ImportError):
            metadata_dict = {}
        
        result.append(models.PodcastProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            metadata=models.PodcastMetadata(**metadata_dict),
            pipeline_state=project.pipeline_state,
            current_segment_index=project.current_segment_index,
            total_segments=project.total_segments,
            completed_count=project.completed_count,
            failed_count=project.failed_count,
            skipped_count=project.skipped_count,
            percentage=project.completed_count / project.total_segments if project.total_segments > 0 else 0.0,
            story_id=project.story_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            started_at=project.started_at,
            completed_at=project.completed_at,
        ))
    
    return result


@app.get("/podcast/projects/{project_id}")
async def get_podcast_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get specific podcast project with segments."""
    project = db.query(DBPodcastProject).filter_by(id=project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        import json
        metadata_dict = json.loads(project.metadata_json)
    except (json.JSONDecodeError, ImportError):
        metadata_dict = {}
    
    segments = db.query(DBPodcastSegment).filter_by(
        project_id=project_id
    ).order_by(DBPodcastSegment.segment_order).all()
    
    segment_responses = []
    for segment in segments:
        try:
            gen_settings = json.loads(segment.generation_settings) if segment.generation_settings else {}
        except (json.JSONDecodeError, ImportError):
            gen_settings = {}
        
        segment_responses.append(models.PodcastSegment(
            id=segment.id,
            project_id=segment.project_id,
            speaker=segment.speaker,
            text=segment.text,
            profile_id=segment.profile_id,
            model_size=segment.model_size,
            generation_settings=gen_settings,
            marker_type=segment.marker_type,
            marker_value=segment.marker_value,
            segment_order=segment.segment_order,
            status=segment.status,
            error_message=segment.error_message,
            generation_id=segment.generation_id,
            created_at=segment.created_at,
            updated_at=segment.updated_at,
        ))
    
    return models.PodcastProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        metadata=models.PodcastMetadata(**metadata_dict),
        pipeline_state=project.pipeline_state,
        current_segment_index=project.current_segment_index,
        total_segments=project.total_segments,
        completed_count=project.completed_count,
        failed_count=project.failed_count,
        skipped_count=project.skipped_count,
        percentage=project.completed_count / project.total_segments if project.total_segments > 0 else 0.0,
        story_id=project.story_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        started_at=project.started_at,
        completed_at=project.completed_at,
        segments=segment_responses,
    )


@app.post("/podcast/projects")
async def create_podcast_project(
    script_content: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create new podcast project from markdown script."""
    
    try:
        import json
        import yaml
        
        # Parse script
        parser = podcast.PodcastScriptParser()
        metadata, segments = parser.parse(script_content)
        
        # Create story for the podcast
        from .models import StoryCreate
        story_data = StoryCreate(
            name=metadata.title,
            description=metadata.description or f"Podcast: {metadata.title}"
        )
        story = await create_story(story_data, db)
        
        # Create project in database
        project = DBPodcastProject(
            id=str(uuid.uuid4()),
            name=metadata.title,
            description=metadata.description,
            script_content=script_content,
            metadata_json=json.dumps(metadata.dict()),
            pipeline_state="idle",
            current_segment_index=0,
            total_segments=len(segments),
            completed_count=0,
            failed_count=0,
            skipped_count=0,
            story_id=story.id
        )
        
        db.add(project)
        
        # Create segments in database
        for i, segment in enumerate(segments):
            gen_settings = segment.get("generation_settings", {})
            if gen_settings:
                gen_settings_json = json.dumps(gen_settings)
            else:
                gen_settings_json = "{}"
            
            db_segment = DBPodcastSegment(
                id=segment.get("id", str(uuid.uuid4())),
                project_id=project.id,
                speaker=segment.get("speaker", ""),
                text=segment.get("text", ""),
                profile_id=None,  # Will be mapped during validation
                model_size=segment.get("model_size", "1.7B"),
                generation_settings=gen_settings_json,
                marker_type=segment.get("marker_type", "text"),
                marker_value=segment.get("marker_value"),
                segment_order=i,
                status="pending"
            )
            db.add(db_segment)
        
        db.commit()
        
        # Auto-map voice profiles by name
        for segment in segments:
            if segment.get("marker_type") == "text":
                speaker_name = segment.get("speaker")
                if speaker_name:
                    profile = db.query(DBVoiceProfile).filter_by(
                        name=speaker_name
                    ).first()
                    
                    if profile:
                        # Update segment with profile_id
                        db_segment = db.query(DBPodcastSegment).filter_by(
                            id=segment.get("id")
                        ).first()
                        if db_segment:
                            db_segment.profile_id = profile.id
                            db.commit()
        
        # Return created project with segments
        return get_podcast_project(project.id, db)
        
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML parsing error: {str(e)}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON encoding error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/podcast/projects/{project_id}")
async def update_podcast_project(
    project_id: str,
    script_content: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update podcast project (re-import script)."""
    
    project = db.query(DBPodcastProject).filter_by(id=project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        import json
        import yaml
        
        if script_content:
            # Re-parse script
            parser = podcast.PodcastScriptParser()
            metadata, segments = parser.parse(script_content)
            
            # Update project
            project.name = metadata.title
            project.description = metadata.description
            project.script_content = script_content
            project.metadata_json = json.dumps(metadata.dict())
            
            # Delete old story items
            if project.story_id:
                from .database import StoryItem as DBStoryItem
                db.query(DBStoryItem).filter_by(story_id=project.story_id).delete()
            
            # Delete old segments
            db.query(DBPodcastSegment).filter_by(project_id=project_id).delete()
            
            # Create new segments
            for i, segment in enumerate(segments):
                gen_settings = segment.get("generation_settings", {})
                gen_settings_json = json.dumps(gen_settings) if gen_settings else "{}"
                
                db_segment = DBPodcastSegment(
                    id=segment.get("id", str(uuid.uuid4())),
                    project_id=project.id,
                    speaker=segment.get("speaker", ""),
                    text=segment.get("text", ""),
                    profile_id=None,
                    model_size=segment.get("model_size", "1.7B"),
                    generation_settings=gen_settings_json,
                    marker_type=segment.get("marker_type", "text"),
                    marker_value=segment.get("marker_value"),
                    segment_order=i,
                    status="pending"
                )
                db.add(db_segment)
            
            # Reset state
            project.current_segment_index = 0
            project.total_segments = len(segments)
            project.completed_count = 0
            project.failed_count = 0
            project.skipped_count = 0
            project.pipeline_state = "idle"
            project.started_at = None
            project.completed_at = None
            project.updated_at = datetime.utcnow()
            
            db.commit()
        
        return get_podcast_project(project_id, db)
        
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"YAML parsing error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/podcast/projects/{project_id}")
async def delete_podcast_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Delete podcast project."""
    
    project = db.query(DBPodcastProject).filter_by(id=project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete segments
    db.query(DBPodcastSegment).filter_by(project_id=project_id).delete()
    
    # Delete story items
    if project.story_id:
        from .database import StoryItem as DBStoryItem
        db.query(DBStoryItem).filter_by(story_id=project.story_id).delete()
        # Note: We don't delete the story itself as it might be used elsewhere
    
    # Delete project
    db.delete(project)
    db.commit()
    
    return {"status": "ok"}


@app.put("/podcast/projects/{project_id}/segments/{segment_id}")
async def update_podcast_segment(
    project_id: str,
    segment_id: str,
    model_size: Optional[str] = Form(None),
    generation_settings: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update segment configuration (model size, generation settings)."""
    
    segment = db.query(DBPodcastSegment).filter_by(
        id=segment_id,
        project_id=project_id
    ).first()
    
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    
    # Update model size
    if model_size and model_size in ["1.7B", "0.6B"]:
        segment.model_size = model_size
    
    # Update generation settings
    if generation_settings:
        try:
            import json
            json.loads(generation_settings)  # Validate JSON
            segment.generation_settings = generation_settings
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON for generation_settings")
    
    segment.updated_at = datetime.utcnow()
    db.commit()
    
    return models.PodcastSegment(
        id=segment.id,
        project_id=segment.project_id,
        speaker=segment.speaker,
        text=segment.text,
        profile_id=segment.profile_id,
        model_size=segment.model_size,
        generation_settings=json.loads(segment.generation_settings) if segment.generation_settings else {},
        marker_type=segment.marker_type,
        marker_value=segment.marker_value,
        segment_order=segment.segment_order,
        status=segment.status,
        error_message=segment.error_message,
        generation_id=segment.generation_id,
        created_at=segment.created_at,
        updated_at=segment.updated_at,
    )


@app.post("/podcast/projects/{project_id}/start")
async def start_podcast_pipeline(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Start or resume podcast generation pipeline."""
    
    project = db.query(DBPodcastProject).filter_by(id=project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update state to generating
    project.pipeline_state = "generating"
    if project.started_at is None:
        project.started_at = datetime.utcnow()
    db.commit()
    
    # Start pipeline in background
    async def run_pipeline():
        try:
            orchestrator = podcast.get_orchestrator(project_id, db)
            final_state = await orchestrator.start_pipeline()
            print(f"Pipeline completed: {final_state}")
        except Exception as e:
            print(f"Pipeline error: {e}")
            project.pipeline_state = "error"
            db.commit()
    
    asyncio.create_task(run_pipeline())
    
    return {"project_id": project_id, "state": "generating"}


@app.post("/podcast/projects/{project_id}/pause")
async def pause_podcast_pipeline(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Pause pipeline (user initiated)."""
    
    project = db.query(DBPodcastProject).filter_by(id=project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project.pipeline_state = "paused"
    db.commit()
    
    return {"status": "ok"}


@app.get("/podcast/projects/{project_id}/progress")
async def get_podcast_progress(project_id: str):
    """Get pipeline progress via SSE."""
    progress_manager = get_progress_manager()
    
    async def event_generator():
        async for event in progress_manager.subscribe(f"podcast-{project_id}"):
            import json
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/podcast/projects/{project_id}/export")
async def export_podcast_audio(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Export final podcast audio as WAV."""
    
    project = db.query(DBPodcastProject).filter_by(id=project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.pipeline_state != "completed":
        raise HTTPException(status_code=400, detail="Project not completed yet")
    
    try:
        import json
        metadata_dict = json.loads(project.metadata_json)
        
        # Add story_id to metadata for the mixer
        metadata_dict['story_id'] = project.story_id
        
        # Mix and export audio
        from .utils.podcast_audio import PodcastAudioMixer
        mixer = PodcastAudioMixer()
        
        audio_bytes = await mixer.assemble_podcast(project_id, metadata_dict, db)
        
        # Update project
        project.updated_at = datetime.utcnow()
        db.commit()
        
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/wav",
            headers={"Content-Disposition": f'attachment; filename="{project.name}.wav"'}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="voicebox server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=17493, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
