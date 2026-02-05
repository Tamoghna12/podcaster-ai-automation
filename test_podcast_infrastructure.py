"""
Test script to verify podcast production pipeline components.
"""

import sys
import os

# Add parent to path for proper imports
sys.path.insert(0, '/home/lunet/cgtd/Documents/product/voicebox_ai/voicebox')

def test_database_schema():
    """Test database podcast tables exist."""
    print("Testing database schema...")
    
    from backend import database
    
    database.init_db()
    db = next(database.get_db())
    
    # Check tables
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    
    tables = inspector.get_table_names()
    print(f"  Tables found: {tables}")
    
    # Check specific podcast tables
    assert 'podcast_projects' in tables, "Missing podcast_projects table"
    assert 'podcast_segments' in tables, "Missing podcast_segments table"
    
    db.close()
    print("  ✓ Database schema OK\n")


def test_config_module():
    """Test config module directory functions."""
    print("\nTesting config module...")
    
    from backend import config
    
    sfx_dir = config.get_sfx_dir()
    music_dir = config.get_music_dir()
    
    assert sfx_dir.exists(), "SFX directory doesn't exist"
    assert music_dir.exists(), "Music directory doesn't exist"
    
    print(f"  SFX dir: {sfx_dir}")
    print(f"  Music dir: {music_dir}")
    print("  ✓ Config module OK\n")


def test_models_imports():
    """Test that all required models are importable."""
    print("\nTesting model imports...")
    
    from backend import models
    
    required_models = [
        'PodcastMetadata',
        'PodcastSegment',
        'PodcastProjectResponse',
        'PodcastSegment',
    ]
    
    for model in required_models:
        assert hasattr(models, model), f"Missing model: {model}"
        print(f"  ✓ {model}")
    
    print("  ✓ All models importable\n")


def test_database_operations():
    """Test database CRUD operations for podcast."""
    print("\nTesting database CRUD operations...")
    
    from backend import database, models
    
    database.init_db()
    db = next(database.get_db())
    
    # Create test project
    project = database.DBPodcastProject(
        id='test-project-001',
        name='Test Project',
        description='Test podcast project',
        script_content='# Test\nHost1: Hello\nHost2: Hi',
        metadata_json='{}',
        pipeline_state='idle',
    )
    
    db.add(project)
    db.commit()
    
    # Create test segments
    for i in range(3):
        segment = database.DBPodcastSegment(
            id=f'test-seg-{i}',
            project_id=project.id,
            speaker=f'host{(i+1)}',
            text=f'Test segment {i}',
            model_size='1.7B',
            generation_settings='{}',
            segment_order=i,
            status='pending'
        )
        db.add(segment)
    
    db.commit()
    
    # Query back
    projects = db.query(database.DBPodcastProject).all()
    segments = db.query(database.DBPodcastSegment).all()
    
    assert len(projects) == 1, "Should have 1 project"
    assert len(segments) == 3, "Should have 3 segments"
    
    # Cleanup
    db.query(database.DBPodcastSegment).delete()
    db.query(database.DBPodcastProject).delete()
    db.commit()
    db.close()
    
    print(f"  ✓ Created 1 project, 3 segments")
    print("  ✓ Database CRUD OK\n")


def test_yaml_parsing():
    """Test YAML frontmatter parsing."""
    print("\nTesting YAML parsing...")
    
    import yaml
    
    # Test metadata parsing
    yaml_content = """
---
title: "Test Podcast"
speakers:
  host1: "John"
  host2: "Jane"

intro:
  enabled: true
  profile: "host1"
  text: "Intro text"
---
Host1: Hello world!
"""
    
    metadata = yaml.safe_load(yaml_content)
    
    assert metadata['title'] == 'Test Podcast'
    assert 'speakers' in metadata, "Missing speakers"
    assert 'intro' in metadata, "Missing intro"
    assert metadata['intro']['enabled'] == True
    assert metadata['intro']['profile'] == 'host1'
    
    print("  ✓ YAML parsing OK\n")


def main():
    """Run all tests."""
    print("=" * 50)
    print("VOICEBOX PODCAST PIPELINE TESTS")
    print("=" * 50)
    
    try:
        test_database_schema()
        test_config_module()
        test_models_imports()
        test_database_operations()
        test_yaml_parsing()
        
        print("\n" + "=" * 50)
        print("ALL TESTS PASSED!")
        print("=" * 50)
        print("\nCore infrastructure is working!")
        print("\nNext steps:")
        print("1. Add podcast script import endpoint")
        print("2. Add pipeline start/stop endpoints")
        print("3. Implement audio mixing")
        print("4. Create frontend components")
        print("5. Add default audio assets")
        print("\nEstimated remaining work: 4-6 weeks")
        return 0
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
