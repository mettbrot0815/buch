#!/usr/bin/env python3
"""
Professional M4B Audiobook Creator
Converts MP3 chapters into a proper M4B audiobook with:
- Chapter markers
- Embedded cover art
- Full metadata (author, narrator, title)
- Bookmark support
"""

import os
import subprocess
from pathlib import Path
import re
import json

def get_chapter_number(filename):
    """Extract chapter number for sorting."""
    match = re.match(r'(\d+)', Path(filename).stem)
    return int(match.group(1)) if match else 999

def get_chapter_title(filename):
    """Extract chapter title from filename."""
    stem = Path(filename).stem
    # Remove leading number and underscore, clean temp files
    title = re.sub(r'^\d+[_\s]*', '', stem)
    title = re.sub(r'^_', '', title)
    title = re.sub(r'_part\d+$', '', title)
    title = title.replace('_', ' ').strip()
    return title

def create_ffmetadata(chapters_info, output_path):
    """Create FFmetadata file for chapter markers."""
    with open(output_path, 'w') as f:
        f.write(";FFMETADATA1\n")
        f.write("title=Mein Erinnerungsschluessel\n")
        f.write("artist=Christopher\n")
        f.write("album=Mein Erinnerungsschluessel\n")
        f.write("genre=Audiobook\n")
        f.write("year=2024\n")
        f.write("\n")
        
        for ch in chapters_info:
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={int(ch['start'] * 1000)}\n")
            f.write(f"END={int(ch['end'] * 1000)}\n")
            f.write(f"title={ch['title']}\n")
            f.write("\n")

def get_audio_duration(filepath):
    """Get duration of audio file in seconds."""
    result = subprocess.run([
        'ffprobe', '-v', 'quiet', '-show_entries',
        'format=duration', '-of', 'json', str(filepath)
    ], capture_output=True, text=True)
    
    try:
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except:
        return 0.0

def create_m4b_audiobook(
    audio_dir, 
    output_file, 
    title="Mein Erinnerungsschluessel",
    author="Christopher",
    narrator="Conrad (AI)",
    cover_image=None,
    bitrate="128k"
):
    """
    Create a professional M4B audiobook from chapter MP3s.
    """
    audio_dir = Path(audio_dir)
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Get all mp3 files (exclude temp files)
    audio_files = sorted(
        [f for f in audio_dir.glob('*.mp3') if not f.name.startswith('_')],
        key=lambda x: get_chapter_number(x.name)
    )
    
    if not audio_files:
        print("No audio files found!")
        return False
    
    print(f"\n{'='*60}")
    print(f"CREATING M4B AUDIOBOOK")
    print(f"{'='*60}")
    print(f"Title: {title}")
    print(f"Author: {author}")
    print(f"Narrator: {narrator}")
    print(f"Chapters: {len(audio_files)}")
    print(f"Output: {output_file}")
    print(f"{'='*60}\n")
    
    # Calculate chapter timings
    chapters_info = []
    current_time = 0.0
    
    print("Processing chapters:")
    for audio in audio_files:
        duration = get_audio_duration(audio)
        ch_title = get_chapter_title(audio.name)
        ch_num = get_chapter_number(audio.name)
        
        chapters_info.append({
            'file': audio,
            'title': f"Kapitel {ch_num:02d}: {ch_title}",
            'start': current_time,
            'end': current_time + duration,
            'duration': duration
        })
        
        print(f"  [{ch_num:02d}] {current_time:>8.1f}s - {ch_title}")
        current_time += duration
    
    total_duration = current_time
    print(f"\nTotal duration: {total_duration/3600:.2f} hours ({total_duration/60:.1f} minutes)")
    
    # Create concat file for merging
    concat_file = audio_dir / "_concat_list.txt"
    with open(concat_file, 'w') as f:
        for ch in chapters_info:
            f.write(f"file '{ch['file'].name}'\n")
    
    # Create FFmetadata file for chapters
    metadata_file = audio_dir / "_chapters.ffmetadata"
    create_ffmetadata(chapters_info, metadata_file)
    
    # Create M4B with chapters
    print(f"\nCreating M4B audiobook...")
    
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0',
        '-i', str(concat_file),
        '-i', str(metadata_file),
        '-map_metadata', '1',
        '-c:a', 'aac',
        '-b:a', bitrate,
        '-f', 'mp4',
    ]
    
    # Add cover art if provided
    if cover_image and Path(cover_image).exists():
        cmd.extend([
            '-i', str(cover_image),
            '-map', '0:v', '-map', '1:a',
            '-c:v', 'mjpeg',
            '-disposition:v', 'attached_pic',
        ])
    
    # Add metadata
    cmd.extend([
        '-metadata', f'title={title}',
        '-metadata', f'artist={author}',
        '-metadata', f'album={title}',
        '-metadata', f'composer={narrator}',
        '-metadata', 'genre=Audiobook',
        str(output_file)
    ])
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=audio_dir)
    
    if result.returncode != 0:
        print(f"Error creating M4B: {result.stderr}")
        return False
    
    # Cleanup temp files
    concat_file.unlink(missing_ok=True)
    metadata_file.unlink(missing_ok=True)
    
    # Get final file size
    file_size = output_file.stat().st_size / (1024 * 1024)
    
    print(f"\n{'='*60}")
    print(f"SUCCESS!")
    print(f"{'='*60}")
    print(f"File: {output_file}")
    print(f"Size: {file_size:.1f} MB")
    print(f"Duration: {total_duration/3600:.2f} hours")
    print(f"Chapters: {len(chapters_info)}")
    print(f"{'='*60}")
    
    # Save chapter list for reference
    chapters_file = output_file.with_suffix('.chapters.txt')
    with open(chapters_file, 'w', encoding='utf-8') as f:
        f.write(f"Chapters for: {title}\n")
        f.write(f"Author: {author}\n")
        f.write(f"Narrator: {narrator}\n")
        f.write("="*60 + "\n\n")
        for ch in chapters_info:
            hours = int(ch['start'] // 3600)
            minutes = int((ch['start'] % 3600) // 60)
            seconds = int(ch['start'] % 60)
            f.write(f"[{hours:02d}:{minutes:02d}:{seconds:02d}] {ch['title']}\n")
    
    print(f"\nChapter list saved to: {chapters_file}")
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Create professional M4B audiobook')
    parser.add_argument('--input', '-i', default='audio', help='Input directory with MP3 chapters')
    parser.add_argument('--output', '-o', default='audiobook.m4b', help='Output M4B file')
    parser.add_argument('--title', '-t', default='Mein Erinnerungsschluessel', help='Book title')
    parser.add_argument('--author', '-a', default='Christopher', help='Author name')
    parser.add_argument('--narrator', '-n', default='Conrad (AI)', help='Narrator name')
    parser.add_argument('--cover', '-c', default=None, help='Cover image file (JPG/PNG)')
    parser.add_argument('--bitrate', '-b', default='128k', help='Audio bitrate (default: 128k)')
    
    args = parser.parse_args()
    
    create_m4b_audiobook(
        args.input,
        args.output,
        title=args.title,
        author=args.author,
        narrator=args.narrator,
        cover_image=args.cover,
        bitrate=args.bitrate
    )
