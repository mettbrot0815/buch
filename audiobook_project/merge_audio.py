#!/usr/bin/env python3
"""
Merge all chapter audio files into a single audiobook file.
Also creates chapter markers for proper audiobook navigation.
"""

import os
import subprocess
from pathlib import Path
import re

def get_chapter_number(filename):
    """Extract chapter number for sorting."""
    match = re.match(r'(\d+)', Path(filename).stem)
    return int(match.group(1)) if match else 999

def get_chapter_title(filename):
    """Extract chapter title from filename."""
    stem = Path(filename).stem
    # Remove leading number and underscore
    title = re.sub(r'^\d+[_\s]*', '', stem)
    # Clean up
    title = title.replace('_', ' ').strip()
    return title

def merge_audiobook(audio_dir, output_file, title="Mein Erinnerungsschluessel"):
    """Merge all audio files into a single audiobook."""
    audio_dir = Path(audio_dir)
    output_file = Path(output_file)
    
    # Get all mp3 files
    audio_files = sorted(
        [f for f in audio_dir.glob('*.mp3') if not f.name.startswith('_')],
        key=lambda x: get_chapter_number(x.name)
    )
    
    if not audio_files:
        print("No audio files found!")
        return
    
    print(f"\n{'='*60}")
    print(f"MERGING AUDIOBOOK")
    print(f"{'='*60}")
    print(f"Chapters: {len(audio_files)}")
    print(f"Output: {output_file}")
    print(f"{'='*60}\n")
    
    # Create ffmpeg concat list
    concat_file = audio_dir / "_concat_list.txt"
    with open(concat_file, 'w') as f:
        for audio in audio_files:
            f.write(f"file '{audio.name}'\n")
    
    # Get durations for chapter markers
    durations = []
    current_time = 0.0
    
    print("Chapter markers:")
    for audio in audio_files:
        # Get duration using ffprobe
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', str(audio)
        ], capture_output=True, text=True)
        
        try:
            duration = float(result.stdout.strip())
        except:
            duration = 0.0
        
        ch_title = get_chapter_title(audio.name)
        ch_num = get_chapter_number(audio.name)
        
        print(f"  [{ch_num:02d}] {current_time:.2f}s - {ch_title}")
        durations.append({
            'file': audio.name,
            'title': ch_title,
            'start': current_time,
            'duration': duration
        })
        current_time += duration
    
    # Merge all files
    print(f"\nMerging {len(audio_files)} files...")
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', str(concat_file), '-c', 'copy', str(output_file)
    ], capture_output=True)
    
    # Clean up
    concat_file.unlink()
    
    print(f"\n[DONE] Created: {output_file}")
    print(f"Total duration: {current_time/3600:.2f} hours")
    
    # Save chapter markers to file
    markers_file = output_file.with_suffix('.chapters.txt')
    with open(markers_file, 'w') as f:
        f.write("Chapter markers for audiobook\n")
        f.write("="*50 + "\n\n")
        for d in durations:
            hours = int(d['start'] // 3600)
            minutes = int((d['start'] % 3600) // 60)
            seconds = int(d['start'] % 60)
            f.write(f"[{hours:02d}:{minutes:02d}:{seconds:02d}] Chapter {get_chapter_number(d['file']):02d}: {d['title']}\n")
    
    print(f"Chapter markers saved to: {markers_file}")
    
    return durations

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Merge audio files into audiobook')
    parser.add_argument('--input', '-i', default='audio', help='Input audio directory')
    parser.add_argument('--output', '-o', default='audiobook.mp3', help='Output audiobook file')
    parser.add_argument('--title', '-t', default='Mein Erinnerungsschluessel', help='Audiobook title')
    
    args = parser.parse_args()
    
    merge_audiobook(args.input, args.output, args.title)
