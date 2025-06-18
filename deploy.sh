#!/bin/bash


set -e  # Exit on any error

echo "🚀 Starting AFI Tracker deployment..."

# Pull latest changes
echo "📥 Pulling latest changes from git..."
git pull

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install/update requirements
echo "📦 Installing/updating requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Kill existing tmux session if it exists
echo "🔄 Checking for existing tmux session..."
if tmux has-session -t afi_tracker 2>/dev/null; then
    echo "⚠️  Killing existing tmux session..."
    tmux kill-session -t afi_tracker
fi

# Launch app in tmux session
echo "🎯 Launching AFI Tracker in tmux session..."
tmux new-session -d -s afi_tracker -c "$(pwd)" "source venv/bin/activate && python main.py"

echo "✅ Deployment complete!"
echo "📺 To view the app logs, run: tmux attach -t afi_tracker"
echo "🛑 To stop the app, run: tmux kill-session -t afi_tracker"