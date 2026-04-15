# Professional Audiobook Project - "Mein Erinnerungsschluessel"

Creates a **professional M4B audiobook** with:
- Chapter markers (skip between chapters)
- Bookmarks (remembers playback position)
- Embedded cover art
- Full metadata (author, narrator, year)

## Quick Start

```bash
# 1. Activate virtual environment
source ../audiobook_venv/bin/activate

# 2. Generate audio for all chapters (with male voice)
python generate_audiobook.py --voice conrad

# 3. Create professional M4B audiobook
python create_m4b.py --output "Mein_Erinnerungsschluessel.m4b"
```

## Output Files

| File | Description |
|------|-------------|
| `audio/*.mp3` | Individual chapter audio files |
| `Mein_Erinnerungsschluessel.m4b` | **Final audiobook** (M4B with chapters) |
| `Mein_Erinnerungsschluessel.chapters.txt` | Chapter markers list |

## Why M4B (Not MP3)?

| Feature | MP3 | M4B |
|---------|-----|-----|
| Chapter navigation | No | Yes |
| Resume playback | No | Yes |
| Embedded cover art | Limited | Full |
| Industry standard | No | Yes |
| Platforms | Basic players | Apple Books, iTunes, etc. |

## Available German Voices

| Voice | ID | Gender | Best For |
|-------|-----|--------|----------|
| **conrad** | de-DE-ConradNeural | Male | Default for male author |
| killian | de-DE-KillianNeural | Male | Alternative male |
| katja | de-DE-KatjaNeural | Female | Female narrator |
| amala | de-DE-AmalaNeural | Female | Friendly female |

## Commands

### Generate Audio

```bash
# All chapters (male voice - recommended for male author)
python generate_audiobook.py --voice conrad

# Specific range
python generate_audiobook.py --start 1 --end 10 --voice conrad

# List voices
python generate_audiobook.py --list-voices
```

### Create M4B Audiobook

```bash
# Basic M4B creation
python create_m4b.py --output audiobook.m4b

# With cover art
python create_m4b.py --output audiobook.m4b --cover cover.jpg

# Full metadata
python create_m4b.py \
  --output "Mein_Erinnerungsschluessel.m4b" \
  --title "Mein Erinnerungsschluessel" \
  --author "Christopher" \
  --narrator "Conrad (AI)" \
  --cover cover.jpg
```

## Industry Standards Met

Based on ACX/Audible requirements:

| Requirement | Setting |
|-------------|---------|
| Format | M4B (MPEG-4 Audio Book) |
| Sample rate | 44.1 kHz |
| Bitrate | 128 kbps AAC |
| Channels | Mono |
| Chapter markers | Yes |
| Metadata | Full ID3/Atom tags |

## Project Structure

```
audiobook_project/
├── generate_audiobook.py   # TTS generation (Edge TTS)
├── create_m4b.py           # M4B creator with chapters
├── merge_audio.py          # Alternative: simple MP3 merge
└── README.md               # This file

audio/                      # Generated chapter MP3s
├── 00_Vorwort.mp3
├── 01_Das Herz...mp3
└── ... (67 chapters)

Mein_Erinnerungsschluessel.m4b  # Final audiobook
```

## Requirements

- Python 3.8+
- edge-tts (`pip install edge-tts`)
- ffmpeg (for audio processing)

## Tips

1. **Male author = male voice** - Conrad is recommended
2. **M4B > MP3** - Always create M4B for professional result
3. **Resume works** - M4B remembers where you stopped
4. **Cover art** - Add a JPG cover for visual appeal
5. **Bitrate** - 128k is ideal for audiobooks (smaller files, good quality)
