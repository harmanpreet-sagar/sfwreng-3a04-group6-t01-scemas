# SFWRENG 3A04 - Group 6 - Tutorial 01

Software Design III Project Repository

## Project Structure

```
├── docs/                      # All documentation and design artifacts
│   ├── diagrams/             # UML diagrams and design models
│   │   ├── plantuml/         # PlantUML source files (.puml)
│   │   │   ├── usecase/      # Use case diagrams
│   │   │   ├── class/        # Class diagrams
│   │   │   ├── sequence/     # Sequence diagrams
│   │   │   ├── activity/     # Activity diagrams
│   │   │   └── state/        # State diagrams
│   │   ├── drawio/           # Draw.io source files
│   │   └── compiled/         # Generated diagram images (PNG/SVG)
│   ├── reports/              # Project deliverables and reports
│   └── images/               # Screenshots, mockups, and other images
│       ├── screenshots/
│       └── mockups/
├── src/                      # Source code (to be added)
├── tests/                    # Test files
└── scripts/                  # Build and utility scripts
```

## Getting Started

### Prerequisites

- PlantUML (for diagram generation)
- Draw.io (for editing .drawio files)

### Compiling PlantUML Diagrams

To generate PNG images from PlantUML files:

```bash
# Compile a single diagram
plantuml docs/diagrams/plantuml/usecase/usecase_diagram_2_revised.puml -o ../compiled

# Compile all diagrams
plantuml docs/diagrams/plantuml/**/*.puml -o ../compiled
```

## Team

Group 6 - Tutorial 01

## Course Information

**Course:** SFWRENG 3A04 - Software Design III  
**Term:** Winter 2026  
**Institution:** McMaster University
