#!/bin/bash
# Voicebox Backend Setup Script for Linux + Nvidia GPU

set -e

echo "==========================================="
echo "  Voicebox Backend Setup"
echo "==========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi
echo "✓ Python 3 installed"
echo ""

# Create virtual environment
VENV_DIR="voicebox_env"
if [ -d "$VENV_DIR" ]; then
    echo "ℹ  Virtual environment already exists at $VENV_DIR"
    read -p "Recreate it? (y/n): " -n 1 -r
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing old venv..."
        rm -rf "$VENV_DIR"
    else
        echo "Using existing venv"
        source "$VENV_DIR/bin/activate"
        SKIP_VENV=1
    fi
fi

if [ ! "$SKIP_VENV" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    
    echo "✓ Virtual environment created"
    echo ""
    
    # Activate venv
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to activate virtual environment"
        exit 1
    fi
    
    echo "✓ Virtual environment activated"
    echo ""
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    echo "Please check requirements.txt and try again"
    exit 1
fi

echo "✓ All dependencies installed"
echo ""

# Check CUDA availability
echo "Checking CUDA (Nvidia GPU) availability..."
python3 << 'EOF'
import torch

if torch.cuda.is_available():
    print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
    print(f"  Total GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    print(f"  Current allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")
else:
    print("⚠ CUDA not available - will use CPU")

EOF

if [ $? -ne 0 ]; then
    echo "❌ CUDA check failed"
fi
echo ""

# Verify imports
echo "Verifying core imports..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

failed_imports = []

# Try each import
try:
    import fastapi
    print("✓ FastAPI")
except ImportError as e:
    print(f"❌ FastAPI: {e}")
    failed_imports.append("FastAPI")

try:
    import sqlalchemy
    print("✓ SQLAlchemy")
except ImportError as e:
    print(f"❌ SQLAlchemy: {e}")
    failed_imports.append("SQLAlchemy")

try:
    import yaml
    print("✓ PyYAML")
except ImportError as e:
    print(f"❌ PyYAML: {e}")
    failed_imports.append("PyYAML")

try:
    import torch
    print("✓ PyTorch")
except ImportError as e:
    print(f"❌ PyTorch: {e}")
    failed_imports.append("PyTorch")

try:
    import librosa
    print("✓ Librosa")
except ImportError as e:
    print(f"❌ Librosa: {e}")
    failed_imports.append("Librosa")

try:
    import soundfile
    print("✓ SoundFile")
except ImportError as e:
    print(f"❌ SoundFile: {e}")
    failed_imports.append("SoundFile")

try:
    from backend import database, models, podcast, config
    print("✓ database module")
    print("✓ models module")
    print("✓ podcast module")
    print("✓ config module")
except ImportError as e:
    print(f"❌ Backend modules: {e}")
    failed_imports.append("Backend modules")

if failed_imports:
    print("")
    print(f"❌ {len(failed_imports)} import(s) failed")
    sys.exit(1)

print("")
print("✓ All imports verified")
print("")
EOF

if [ $? -ne 0 ]; then
    echo "❌ Import verification failed"
    exit 1
fi

# Check database initialization
echo ""
echo "Checking database initialization..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from backend import database

try:
    database.init_db()
    db = next(database.get_db())
    
    # Check tables
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    
    required_tables = ['podcast_projects', 'podcast_segments']
    missing_tables = [t for t in required_tables if t not in tables]
    
    if missing_tables:
        print(f"❌ Missing database tables: {missing_tables}")
        sys.exit(1)
    
    print("✓ Database tables verified")
    print(f"  Podcast tables: {[t for t in tables if 'podcast' in t]}")
    db.close()
    
except Exception as e:
    print(f"❌ Database check failed: {e}")
    sys.exit(1)

EOF

if [ $? -ne 0 ]; then
    echo "❌ Database check failed"
    exit 1
fi

# Check data directories
echo ""
echo "Checking data directories..."
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

from backend import config
import os

directories = [
    ('Profiles', config.get_profiles_dir()),
    ('Generations', config.get_generations_dir()),
    ('Cache', config.get_cache_dir()),
    ('SFX', config.get_sfx_dir()),
    ('Music', config.get_music_dir()),
]

for name, path in directories:
    if path.exists():
        print(f"✓ {name}: {path}")
    else:
        print(f"❌ {name}: {path} (will be created on first use)")
        try:
            path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {path}")
        except Exception as e:
            print(f"Failed to create {path}: {e}")

EOF

echo ""
echo "==========================================="
echo "  Setup Complete!"
echo "==========================================="
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment:"
echo "     source $VENV_DIR/bin/activate"
echo ""
echo "  2. Start server:"
echo "     python3 main.py"
echo ""
echo "  3. Test endpoints:"
echo "     curl http://localhost:17493/health"
echo "     curl http://localhost:17493/podcast/projects"
echo ""
echo "  To deactivate virtual environment:"
echo "     deactivate"
echo ""
