# Video Processing Skills

Claude Code Skills for cryptocurrency/financial analysis video production.

## 🎬 Skills Overview

This repository contains video production skills for cryptocurrency market analysis content creation.

### Core Video Processing

| Skill | Description |
|-------|-------------|
| **video1-processing** | Video1 YouTube Traditional (1.1x speed, deduplication, standard version) |
| **video2-processing** | Video2 Simplified (1.1x speed, deduplication + ending prompt) |
| **video3-processing** | Video3 Subtitle Version (1.1x + 2s simplified cover + burned subtitles) |
| **video4-processing** | Video4 Editing Source (1.1x speed + subtitles, no cover) |

### Subtitle Generation

| Skill | Description |
|-------|-------------|
| **jz-subtitle** | Cryptocurrency subtitle generation (VolcEngine ASR + specialized corrections) |
| **extract-1.1x-audio** | Extract audio from video and accelerate to 1.1x speed |

### Cover Generation

| Skill | Description |
|-------|-------------|
| **generate-cover-v2** | YouTube cover generation with dual traditional/simplified versions |
| **ethereum-cover** | Ethereum-specific cover generation |

### Metadata Generation

| Skill | Description |
|-------|-------------|
| **generate-meta** | Multi-platform title and description generation (YouTube, Bilibili, Weibo, etc.) |
| **coin-metadata** | Cryptocurrency video metadata generation |

### Ethereum Specialized

| Skill | Description |
|-------|-------------|
| **ethereum-video** | Ethereum-specific video editing |

### Additional Video Tools

| Skill | Description |
|-------|-------------|
| **clean-pipeline** | Clean video pipeline directories |
| **telegram-download** | Download videos from Telegram server |
| **clip-coins** | Individual cryptocurrency video clips |
| **short-video** | Cryptocurrency market short videos |
| **asset-videos** | Asset video auto-generation |
| **asset-timeline-analyzer** | Asset timeline analyzer |
| **analyze-assets** | Cryptocurrency video asset timeline analysis |

## 📋 Requirements

- Python 3.9+
- Node.js 18+
- ffmpeg (for video/audio processing)
- VolcEngine API key (for ASR)
- ImageMagick (for cover generation)

## 🚀 Quick Start

### Video Production Workflow

```bash
# 1. Extract audio at 1.1x speed
python extract-1.1x-audio/scripts/extract_audio.py

# 2. Generate subtitles with human review
cd jz-subtitle
./scripts/volcengine_api.sh audio.wav
node scripts/process_subtitles.js volcengine_result.json output/ --draft
# ... review and edit draft.txt ...
node scripts/process_subtitles.js volcengine_result.json output/ --final

# 3. Generate metadata
node generate-meta/scripts/generate_meta.js

# 4. Generate cover (with title selection)
node generate-cover-v2/scripts/generate_cover.js

# 5. Process videos
# Video1: YouTube Traditional
# Video2: Simplified + Ending
# Video3: Subtitle Version
# Video4: Editing Source
```

## 📁 File Structure

```
video-processing-skills/
├── video1-processing/      # YouTube Traditional video
├── video2-processing/      # Simplified video
├── video3-processing/      # Subtitle version
├── video4-processing/      # Editing source
├── jz-subtitle/            # Subtitle generation
├── extract-1.1x-audio/      # Audio extraction
├── generate-cover-v2/      # Cover generation
├── ethereum-cover/         # Ethereum covers
├── generate-meta/          # Metadata generation
├── coin-metadata/          # Coin metadata
├── ethereum-video/         # Ethereum videos
├── clean-pipeline/         # Pipeline cleanup
├── telegram-download/      # Telegram downloads
├── clip-coins/             # Coin clips
├── short-video/            # Short videos
├── asset-videos/           # Asset videos
├── asset-timeline-analyzer/ # Timeline analysis
└── analyze-assets/         # Asset analysis
```

## 🔧 Configuration

### VolcEngine API (for subtitles)

Create `.env` file in `jz-subtitle/`:
```
VOLCENGINE_API_KEY=your_api_key_here
```

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt  # (if available)
npm install  # (for Node.js scripts)

# Verify installations
ffmpeg -version
node --version
python3 --version
```

## 📝 Workflow Integration

These skills are designed for a complete cryptocurrency video production pipeline:

1. **Content Creation** → Script recording
2. **Audio Processing** → Extract and accelerate audio
3. **Subtitle Generation** → ASR + specialized corrections
4. **Metadata** → Multi-platform titles and descriptions
5. **Cover Design** → Auto-generated covers
6. **Video Processing** → Multiple output versions
7. **Distribution** → YouTube, Bilibili, Weibo, etc.

## 🎯 Specialized Features

### Cryptocurrency Terminology

The subtitle system includes specialized corrections for:
- Trading terminology (long, short, stop-loss, leverage)
- Technical analysis ( Elliott waves, support, resistance)
- Coin names (Bitcoin, Ethereum, specific tokens)
- Common ASR errors in financial context

### Multi-Platform Support

- **YouTube**: Traditional Chinese + cover
- **Bilibili**: Simplified Chinese + subtitles
- **Weibo/Twitter**: Optimized titles and descriptions
- **Facebook**: Platform-specific formatting

## 📄 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🔗 Related Projects

- [Claude Code](https://github.com/anthropics/claude-code) - The AI coding assistant
- [gstack](https://github.com/garrytan/gstack) - Development workflow skills

---

**Note**: These skills are optimized for Chinese cryptocurrency market analysis content. Adjustments may be needed for other languages or content types.
