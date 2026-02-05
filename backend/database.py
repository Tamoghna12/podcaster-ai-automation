"""
SQLite database ORM using SQLAlchemy.
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import uuid
from pathlib import Path

from . import config

Base = declarative_base()


class VoiceProfile(Base):
    """Voice profile database model."""
    __tablename__ = "profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    language = Column(String, default="en")
    avatar_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProfileSample(Base):
    """Voice profile sample database model."""
    __tablename__ = "profile_samples"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String, ForeignKey("profiles.id"), nullable=False)
    audio_path = Column(String, nullable=False)
    reference_text = Column(Text, nullable=False)


class Generation(Base):
    """Generation history database model."""
    __tablename__ = "generations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String, ForeignKey("profiles.id"), nullable=False)
    text = Column(Text, nullable=False)
    language = Column(String, default="en")
    audio_path = Column(String, nullable=False)
    duration = Column(Float, nullable=False)
    seed = Column(Integer)
    instruct = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Story(Base):
    """Story database model."""
    __tablename__ = "stories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StoryItem(Base):
    """Story item database model (links generations to stories)."""
    __tablename__ = "story_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String, ForeignKey("stories.id"), nullable=False)
    generation_id = Column(String, ForeignKey("generations.id"), nullable=False)
    start_time_ms = Column(Integer, nullable=False, default=0)  # Milliseconds from story start
    track = Column(Integer, nullable=False, default=0)  # Track number (0 = main track)
    trim_start_ms = Column(Integer, nullable=False, default=0)  # Milliseconds trimmed from start
    trim_end_ms = Column(Integer, nullable=False, default=0)  # Milliseconds trimmed from end
    created_at = Column(DateTime, default=datetime.utcnow)


class Project(Base):
    """Audio studio project database model."""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    data = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AudioChannel(Base):
    """Audio channel (bus) database model."""
    __tablename__ = "audio_channels"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChannelDeviceMapping(Base):
    """Mapping between channels and OS audio devices."""
    __tablename__ = "channel_device_mappings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    channel_id = Column(String, ForeignKey("audio_channels.id"), nullable=False)
    device_id = Column(String, nullable=False)  # OS device identifier


class ProfileChannelMapping(Base):
    """Mapping between voice profiles and audio channels (many-to-many)."""
    __tablename__ = "profile_channel_mappings"
    
    profile_id = Column(String, ForeignKey("profiles.id"), primary_key=True)
    channel_id = Column(String, ForeignKey("audio_channels.id"), primary_key=True)


# Database setup will be initialized in init_db()
engine = None
SessionLocal = None
_db_path = None


class PodcastProject(Base):
    """Podcast production project - persisted in database."""
    __tablename__ = "podcast_projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)  # From metadata.title
    description = Column(Text)  # Optional: summary or episode info
    script_content = Column(Text, nullable=False)  # Original markdown script
    metadata_json = Column(Text, nullable=False)  # Serialized PodcastMetadata
    
    # Pipeline state (for resumability)
    pipeline_state = Column(String, default="idle")  # idle, generating, paused, completed, error
    current_segment_index = Column(Integer, default=0)
    total_segments = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    skipped_count = Column(Integer, default=0)
    
    # Story linking (final output)
    story_id = Column(String, ForeignKey("stories.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)  # When pipeline started
    completed_at = Column(DateTime, nullable=True)  # When pipeline completed


class PodcastSegment(Base):
    """Individual podcast segment - persisted in database."""
    __tablename__ = "podcast_segments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("podcast_projects.id"), nullable=False)
    
    # Content
    speaker = Column(String, nullable=False)  # e.g., "host1", "jane"
    text = Column(Text, nullable=False)
    
    # Voice profile mapping
    profile_id = Column(String, ForeignKey("profiles.id"), nullable=True)
    
    # Model configuration (per-segment)
    model_size = Column(String, default="1.7B")  # "1.7B" or "0.6B"
    generation_settings = Column(Text, nullable=True)  # JSON: speed, pitch, etc.
    
    # Marker type
    marker_type = Column(String, default="text")  # text, sound_effect, music_cue
    marker_value = Column(Text, nullable=True)  # For markers: effect name, music cue
    
    # Ordering
    segment_order = Column(Integer, nullable=False)
    
    # State
    status = Column(String, default="pending")  # pending, generating, completed, failed, skipped
    error_message = Column(Text, nullable=True)
    
    # Generated output
    generation_id = Column(String, ForeignKey("generations.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    """Initialize database tables."""
    global engine, SessionLocal, _db_path

    _db_path = config.get_db_path()
    _db_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{_db_path}",
        connect_args={"check_same_thread": False},
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Run migrations before creating tables
    _run_migrations(engine)
    
    Base.metadata.create_all(bind=engine)
    
    # Create default channel if it doesn't exist
    db = SessionLocal()
    try:
        default_channel = db.query(AudioChannel).filter(AudioChannel.is_default == True).first()
        if not default_channel:
            default_channel = AudioChannel(
                id=str(uuid.uuid4()),
                name="Default",
                is_default=True
            )
            db.add(default_channel)
            
            # Assign all existing profiles to default channel
            profiles = db.query(VoiceProfile).all()
            for profile in profiles:
                mapping = ProfileChannelMapping(
                    profile_id=profile.id,
                    channel_id=default_channel.id
                )
                db.add(mapping)
            
            db.commit()
    finally:
        db.close()


def _run_migrations(engine):
    """Run database migrations."""
    from sqlalchemy import inspect, text
    
    inspector = inspect(engine)
    
    # Check if story_items table exists
    if 'story_items' not in inspector.get_table_names():
        return  # Table doesn't exist yet, will be created fresh
    
    # Get columns in story_items table
    columns = {col['name'] for col in inspector.get_columns('story_items')}
    
    # Migration: Remove position column and ensure start_time_ms exists
    # SQLite doesn't support DROP COLUMN easily, so we recreate the table
    if 'position' in columns:
        print("Migrating story_items: removing position column, using start_time_ms")
        
        with engine.connect() as conn:
            # Check if start_time_ms already exists
            has_start_time = 'start_time_ms' in columns
            
            if not has_start_time:
                # First, add the new column temporarily
                conn.execute(text("ALTER TABLE story_items ADD COLUMN start_time_ms INTEGER DEFAULT 0"))
                
                # Calculate timecodes from position ordering
                result = conn.execute(text("""
                    SELECT si.id, si.story_id, si.position, g.duration
                    FROM story_items si
                    JOIN generations g ON si.generation_id = g.id
                    ORDER BY si.story_id, si.position
                """))
                
                rows = result.fetchall()
                
                current_story_id = None
                current_time_ms = 0
                
                for row in rows:
                    item_id, story_id, position, duration = row
                    
                    if story_id != current_story_id:
                        current_story_id = story_id
                        current_time_ms = 0
                    
                    conn.execute(
                        text("UPDATE story_items SET start_time_ms = :time WHERE id = :id"),
                        {"time": current_time_ms, "id": item_id}
                    )
                    
                    current_time_ms += int(duration * 1000) + 200
                
                conn.commit()
            
            # Now recreate the table without the position column
            # 1. Create new table
            conn.execute(text("""
                CREATE TABLE story_items_new (
                    id VARCHAR PRIMARY KEY,
                    story_id VARCHAR NOT NULL,
                    generation_id VARCHAR NOT NULL,
                    start_time_ms INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME,
                    FOREIGN KEY (story_id) REFERENCES stories(id),
                    FOREIGN KEY (generation_id) REFERENCES generations(id)
                )
            """))
            
            # 2. Copy data
            conn.execute(text("""
                INSERT INTO story_items_new (id, story_id, generation_id, start_time_ms, created_at)
                SELECT id, story_id, generation_id, start_time_ms, created_at FROM story_items
            """))
            
            # 3. Drop old table
            conn.execute(text("DROP TABLE story_items"))
            
            # 4. Rename new table
            conn.execute(text("ALTER TABLE story_items_new RENAME TO story_items"))
            
            conn.commit()
            print("Migrated story_items table to use start_time_ms (removed position column)")
    
    # Migration: Add track column if it doesn't exist
    # Re-check columns after potential position migration
    columns = {col['name'] for col in inspector.get_columns('story_items')}
    if 'track' not in columns:
        print("Migrating story_items: adding track column")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE story_items ADD COLUMN track INTEGER NOT NULL DEFAULT 0"))
            conn.commit()
            print("Added track column to story_items")
    
    # Migration: Add trim columns if they don't exist
    # Re-check columns after potential track migration
    columns = {col['name'] for col in inspector.get_columns('story_items')}
    if 'trim_start_ms' not in columns:
        print("Migrating story_items: adding trim_start_ms column")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE story_items ADD COLUMN trim_start_ms INTEGER NOT NULL DEFAULT 0"))
            conn.commit()
            print("Added trim_start_ms column to story_items")
    
    columns = {col['name'] for col in inspector.get_columns('story_items')}
    if 'trim_end_ms' not in columns:
        print("Migrating story_items: adding trim_end_ms column")
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE story_items ADD COLUMN trim_end_ms INTEGER NOT NULL DEFAULT 0"))
            conn.commit()
            print("Added trim_end_ms column to story_items")

    # Migration: Add avatar_path to profiles table
    if 'profiles' in inspector.get_table_names():
        columns = {col['name'] for col in inspector.get_columns('profiles')}
        if 'avatar_path' not in columns:
            print("Migrating profiles: adding avatar_path column")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE profiles ADD COLUMN avatar_path VARCHAR"))
                conn.commit()
                print("Added avatar_path column to profiles")
    
    # Migration: Create podcast_projects table
    if 'podcast_projects' not in inspector.get_table_names():
        print("Creating podcast_projects table")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE podcast_projects (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    description TEXT,
                    script_content TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    pipeline_state VARCHAR DEFAULT 'idle',
                    current_segment_index INTEGER DEFAULT 0,
                    total_segments INTEGER DEFAULT 0,
                    completed_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    skipped_count INTEGER DEFAULT 0,
                    story_id VARCHAR,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    started_at DATETIME,
                    completed_at DATETIME,
                    FOREIGN KEY (story_id) REFERENCES stories(id)
                )
            """))
            conn.commit()
            print("Created podcast_projects table")
    
    # Migration: Create podcast_segments table
    if 'podcast_segments' not in inspector.get_table_names():
        print("Creating podcast_segments table")
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE podcast_segments (
                    id VARCHAR PRIMARY KEY,
                    project_id VARCHAR NOT NULL,
                    speaker VARCHAR NOT NULL,
                    text TEXT NOT NULL,
                    profile_id VARCHAR,
                    model_size VARCHAR DEFAULT '1.7B',
                    generation_settings TEXT,
                    marker_type VARCHAR DEFAULT 'text',
                    marker_value TEXT,
                    segment_order INTEGER NOT NULL,
                    status VARCHAR DEFAULT 'pending',
                    error_message TEXT,
                    generation_id VARCHAR,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES podcast_projects(id),
                    FOREIGN KEY (profile_id) REFERENCES profiles(id),
                    FOREIGN KEY (generation_id) REFERENCES generations(id)
                )
            """))
            conn.commit()
            print("Created podcast_segments table")
    
    # Migration: Add indexes for podcast_segments
    if 'podcast_segments' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('podcast_segments')]
        
        if 'idx_podcast_segments_project' not in existing_indexes:
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE INDEX idx_podcast_segments_project 
                    ON podcast_segments(project_id)
                """))
                conn.commit()
                print("Created index idx_podcast_segments_project")
        
        if 'idx_podcast_segments_order' not in existing_indexes:
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE INDEX idx_podcast_segments_order 
                    ON podcast_segments(project_id, segment_order)
                """))
                conn.commit()
                print("Created index idx_podcast_segments_order")


def get_db():
    """Get database session (generator for dependency injection)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
