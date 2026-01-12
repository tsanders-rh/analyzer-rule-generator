# VHS Demo Recording Guide

Automated terminal demos using [VHS](https://github.com/charmbracelet/vhs) by Charm.

## Installation

### macOS
```bash
brew install vhs
```

### Linux
```bash
# See: https://github.com/charmbracelet/vhs#installation
```

### Verify installation
```bash
vhs --version
```

## Demo Files

### 1. `claude-skill-demo.tape` (SIMULATED - Recommended)
- **Duration**: ~60 seconds
- **Pros**: Fast, predictable, no API calls needed
- **Cons**: Simulated output (not real execution)
- **Use for**: Quick demos, presentations, sharing on social media

```bash
vhs claude-skill-demo.tape
```

**Output files**:
- `claude-skill-demo.gif` - For README, social media
- `claude-skill-demo.mp4` - For presentations
- `claude-skill-demo.webm` - For web embedding

### 2. `claude-skill-demo-real.tape` (REAL EXECUTION)
- **Duration**: ~120 seconds (includes real API calls)
- **Pros**: Shows actual tool output, authentic
- **Cons**: Requires API key, takes longer, uses API credits
- **Use for**: Technical demos, proof of concept, documentation

**Prerequisites**:
```bash
# Ensure API key is set
export ANTHROPIC_API_KEY="your-key-here"

# Activate virtual environment
source venv/bin/activate

# Clean previous outputs
rm -rf demo-output/react-18/
```

**Run**:
```bash
vhs claude-skill-demo-real.tape
```

## Quick Start

### Create a simple demo video

```bash
# 1. Navigate to project
cd ~/Workspace/analyzer-rule-generator

# 2. Run the simulated version
vhs media/claude-skill-demo.tape

# 3. Output files created in current directory
ls -lh claude-skill-demo.*
```

### Preview the GIF
```bash
# macOS
open claude-skill-demo.gif

# Linux
xdg-open claude-skill-demo.gif
```

## Customization

### Edit the tape file

Open `claude-skill-demo.tape` and modify:

**Timing**:
```tape
Sleep 1s      # Wait 1 second
Sleep 500ms   # Wait 500 milliseconds
```

**Typing speed**:
```tape
Type "command"           # Uses default TypingSpeed
Type@100ms "slower"      # Override typing speed for this line
```

**Theme**:
```tape
Set Theme "Monokai"      # Dark theme
Set Theme "Dracula"      # Alternative
Set Theme "GitHub Light" # Light theme
```

**Output formats**:
```tape
Output demo.gif          # Animated GIF
Output demo.mp4          # Video
Output demo.webm         # Web-optimized
Output demo.png          # Single frame
```

### Create a shorter version (30 seconds)

```tape
# Quick 30-second version
Output quick-demo.gif

Set FontSize 18
Set Width 1200
Set Height 600

Hide
Type "cd ~/Workspace/analyzer-rule-generator && source venv/bin/activate && clear"
Enter
Show

Type "# Generate Konveyor migration rules in seconds"
Enter
Sleep 1s

Type "python scripts/generate_rules.py --guide examples/demo-guide-react18.md --source react-17 --target react-18"
Enter
Sleep 2s

Type@300ms "✓ Successfully generated 18 rules in 8 file(s)"
Enter
Sleep 2s
```

## Advanced Features

### Add screenshots/markers
```tape
# Take a screenshot at this point
Screenshot "stage1-complete.png"
```

### Interactive input simulation
```tape
# Simulate user typing and thinking
Type "python scripts/"
Sleep 500ms
Ctrl+C
Sleep 500ms
Type "python scripts/generate_rules.py"
Sleep 300ms
Type " --help"
Enter
```

### Multiple windows
```tape
# Not directly supported, but you can compose videos later
```

## Tips for Best Results

### 1. Font Size
- **Presentation**: 16-18pt
- **Documentation**: 14-16pt
- **Social media**: 18-20pt (larger for visibility)

### 2. Window Size
- **Standard**: 1400x900
- **Widescreen**: 1600x900
- **Square (social)**: 1000x1000

### 3. Timing
- Pause after commands: 1-2 seconds
- Pause after output: 2-3 seconds
- Total video: Keep under 2 minutes for attention span

### 4. Output Format
- **GIF**: Best for GitHub README, Twitter
  - Max size: ~10MB (GitHub limit: 10MB)
  - Optimize: Use fewer frames or shorter duration
- **MP4**: Best for presentations, YouTube
  - Better quality, smaller file size
- **WebM**: Best for web embedding
  - Excellent compression, wide browser support

### 5. Theme Selection
Good themes for demos:
- **Monokai**: Classic, high contrast
- **Dracula**: Popular, easy on eyes
- **Tokyo Night**: Modern, professional
- **Catppuccin**: Pastel, unique

## Troubleshooting

### VHS command not found
```bash
# Install VHS first
brew install vhs  # macOS
```

### Fonts look weird
```bash
# Install a good monospace font
brew tap homebrew/cask-fonts
brew install font-fira-code
```

Then update tape:
```tape
Set FontFamily "Fira Code"
```

### Output too large
```tape
# Reduce dimensions
Set Width 1000
Set Height 600

# Reduce duration
Set PlaybackSpeed 1.5  # Play 1.5x faster
```

### Real execution fails
```bash
# Check API key
echo $ANTHROPIC_API_KEY

# Check venv
source venv/bin/activate

# Test script manually first
python scripts/generate_rules.py --guide examples/demo-guide-react18.md --source react-17 --target react-18 --output /tmp/test-output/
```

## Workflow for Creating Demos

### 1. Test the commands manually
```bash
# Ensure everything works
python scripts/generate_rules.py --guide examples/demo-guide-react18.md --source react-17 --target react-18 --output demo-output/test/
```

### 2. Write the tape file
- Start with simulated version (faster iteration)
- Test timing and appearance
- Switch to real execution when ready

### 3. Generate the videos
```bash
vhs claude-skill-demo.tape
```

### 4. Review and iterate
```bash
open claude-skill-demo.gif
# Too fast? Add more Sleep commands
# Too slow? Reduce Sleep times or increase PlaybackSpeed
```

### 5. Optimize output
```bash
# GIF too large? Use gifsicle
brew install gifsicle
gifsicle -O3 --colors 256 claude-skill-demo.gif -o claude-skill-demo-optimized.gif

# Or reduce dimensions in tape file
```

## Examples in the Wild

Check out these VHS demos for inspiration:
- [Charm VHS examples](https://github.com/charmbracelet/vhs/tree/main/examples)
- [GitHub repos using VHS](https://github.com/search?q=vhs+tape&type=code)

## Integration with CI/CD

### GitHub Actions
```yaml
name: Generate Demo
on: [push]
jobs:
  demo:
    runs-on: ubuntu-latest
    steps:
      - uses: charmbracelet/vhs-action@v1
        with:
          path: 'media/claude-skill-demo.tape'
      - uses: actions/upload-artifact@v3
        with:
          name: demo-videos
          path: '*.gif'
```

## Next Steps

1. **Run the simulated demo**:
   ```bash
   vhs media/claude-skill-demo.tape
   ```

2. **Share it**:
   - Add to README: `![Demo](claude-skill-demo.gif)`
   - Tweet it: Upload the GIF
   - Present it: Use the MP4

3. **Create variants**:
   - Short version (30s) for social media
   - Long version (3min) for tutorials
   - Real version for technical audiences

Happy demo-ing! 🎬
