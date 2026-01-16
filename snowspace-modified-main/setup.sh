#!/bin/bash

# Setup script for Brampton Traffic Scorer

echo "=== Brampton Traffic Scorer Setup ==="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment (optional but recommended)
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "⚠ Could not create virtual environment. Continuing without it..."
else
    echo "✓ Virtual environment created"
    echo ""
    echo "Activating virtual environment..."

    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✓ Virtual environment activated"
    else
        echo "⚠ Could not activate virtual environment"
    fi
fi

echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "✓ Dependencies installed successfully"
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Run the example: python3 traffic_scorer.py"
echo "2. Or try the examples: python3 example_usage.py"
echo ""
echo "Note: First run will download data (~2-5 minutes). Subsequent runs are instant."
echo ""

if [ -d "venv" ]; then
    echo "To activate the virtual environment later, run:"
    echo "  source venv/bin/activate"
    echo ""
fi
