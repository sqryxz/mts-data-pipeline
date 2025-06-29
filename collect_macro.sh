#!/bin/bash

# Macro Data Collection Script for MTS Data Pipeline
# This script loads environment variables and collects macro indicators

# Load environment variables from .env file
if [ -f .env ]; then
    echo "🔑 Loading environment variables from .env..."
    source .env
else
    echo "❌ Error: .env file not found. Please create it with your FRED_API_KEY."
    exit 1
fi

# Check if FRED API key is set
if [ -z "$FRED_API_KEY" ]; then
    echo "❌ Error: FRED_API_KEY not found in environment variables."
    echo "Please add your FRED API key to the .env file."
    exit 1
fi

# Default to 30 days if no argument provided
DAYS=${1:-30}

echo "📊 Collecting macro indicators for the last $DAYS days..."
echo "🔑 Using FRED API Key: ${FRED_API_KEY:0:8}..."
echo ""

# Run the macro collection
python3 main.py --collect-macro --days $DAYS

# Show results
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Collection completed successfully!"
    echo "📁 Data saved to: data/raw/macro/"
    echo ""
    echo "📋 Files created:"
    ls -la data/raw/macro/*.csv 2>/dev/null || echo "   No CSV files found"
else
    echo ""
    echo "❌ Collection failed. Check the logs above for details."
fi 