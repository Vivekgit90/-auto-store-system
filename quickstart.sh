#!/bin/bash
# Quick Start Script for Auto Store Setup System

echo "=================================="
echo "Auto Store Setup - Quick Start"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment
echo ""
echo "Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file"
    echo "⚠ Please edit .env with your credentials"
else
    echo "✓ .env file already exists"
fi

# Initialize database
echo ""
echo "Initializing database..."
python3 -c "from database import Database; from config import CONFIG; db = Database(CONFIG.DB_PATH); print('✓ Database initialized')"

# Create directories
echo ""
echo "Creating directories..."
mkdir -p brand_assets
mkdir -p backups
echo "✓ Directories created"

# Test installation
echo ""
echo "Testing installation..."
python3 -c "import flask, requests, stripe, PIL, schedule; print('✓ All dependencies installed correctly')"

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Run example: python main.py --example"
echo "3. Start webhook server: python webhooks.py"
echo "4. Start cron scheduler: python cron_scheduler.py"
echo ""
echo "Documentation:"
echo "- README.md - General documentation"
echo "- DEPLOYMENT.md - Production deployment guide"
echo "- API_DOCS.md - API reference"
echo ""
