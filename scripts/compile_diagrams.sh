#!/bin/bash
# PlantUML Diagram Compilation Script
# Compiles all .puml files to PNG images in the compiled directory

set -e  # Exit on any error

echo "=========================================="
echo "Compiling PlantUML Diagrams"
echo "=========================================="

# Navigate to project root
cd "$(dirname "$0")/.." || exit 1

# Check if plantuml is installed
if ! command -v plantuml &> /dev/null; then
    echo "❌ Error: PlantUML is not installed"
    echo "   Install with: brew install plantuml (macOS)"
    echo "   Or download from: https://plantuml.com/download"
    exit 1
fi

# Compile all PlantUML diagrams
echo "✓ Compiling class diagrams..."
plantuml docs/diagrams/plantuml/class/*.puml -o ../../../compiled

echo "✓ Compiling sequence diagrams..."
plantuml docs/diagrams/plantuml/sequence/*.puml -o ../../../compiled

echo "✓ Compiling state diagrams..."
plantuml docs/diagrams/plantuml/state/*.puml -o ../../../compiled

echo "✓ Compiling use case diagrams..."
plantuml docs/diagrams/plantuml/usecase/*.puml -o ../../../compiled

echo "✓ Compiling activity diagrams..."
plantuml docs/diagrams/plantuml/activity/*.puml -o ../../../compiled 2>/dev/null || true

echo ""
echo "=========================================="
echo "Compilation Complete!"
echo "=========================================="
echo "Compiled images saved to: docs/diagrams/compiled/"
echo ""
