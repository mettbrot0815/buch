#!/usr/bin/env python3
"""
Audiobook Generator for "Mein Erinnerungsschluessel"
Uses Edge TTS for high-quality German text-to-speech
"""

import os
import asyncio
import edge_tts
import argparse
from pathlib import Path
import re

# Available German voices
GERMAN_VOICES = {
    "amala": "de-DE-AmalaNeural",      # Female - Friendly, Positive
    "conrad": "de-DE-ConradNeural",    # Male - Friendly, Positive
    "florian": "de-DE-FlorianMultilingualNeural",  # Male - Multilingual
    "katja": "de-DE-KatjaNeural",      # Female - Friendly, Positive
    "killian": "de-DE-KillianNeural",  # Male - Friendly, Positive
    "seraphina": "de-DE-SeraphinaMultilingualNeural",  # Female - Multilingual
}

DEFAULT_VOICE = "katja"  # Female voice, warm and friendly

def clean_text(text):
    """Clean text for TTS - remove problematic characters."""
    # Remove BOM and zero-width characters
    text = text.replace('\ufeff', '')
    text = text.replace('\u200b', '')  # Zero-width space
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    # Keep natural sentence breaks
    text = text.strip()
    return text

def split_long_text(text, max_chars=5000):
    """Split long text into smaller chunks for TTS processing."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk += (" " if current_chunk else "") + sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

async def generate_audio_async(text, output_path, voice_name):
    """Generate audio from text using Edge TTS."""
    voice = GERMAN_VOICES.get(voice_name, GERMAN_VOICES[DEFAULT_VOICE])
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def generate_audio(text, output_path, voice_name=DEFAULT_VOICE):
    """Synchronous wrapper for audio generation."""
    asyncio.run(generate_audio_async(text, output_path, voice_name))

def process_chapter(chapter_path, output_dir, voice_name=DEFAULT_VOICE):
    """Process a single chapter file into audio."""
    chapter_path = Path(chapter_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read chapter
    with open(chapter_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Clean text
    text = clean_text(text)
    
    if not text:
        print(f"  [SKIP] Empty content in {chapter_path.name}")
        return None
    
    # Generate output filename
    output_name = chapter_path.stem + ".mp3"
    output_path = output_dir / output_name
    
    # Check if already exists
    if output_path.exists():
        print(f"  [EXISTS] {output_name}")
        return output_path
    
    # Split into chunks if needed
    chunks = split_long_text(text)
    
    print(f"  [PROCESSING] {chapter_path.name}")
    print(f"    - Length: {len(text)} chars, {len(chunks)} chunk(s)")
    
    if len(chunks) == 1:
        # Single chunk - direct generation
        generate_audio(text, str(output_path), voice_name)
    else:
        # Multiple chunks - generate and concatenate
        temp_files = []
        for i, chunk in enumerate(chunks):
            temp_path = output_dir / f"_{chapter_path.stem}_part{i}.mp3"
            print(f"    - Generating part {i+1}/{len(chunks)}...")
            generate_audio(chunk, str(temp_path), voice_name)
            temp_files.append(temp_path)
        
        # Concatenate audio files using ffmpeg
        concat_list = output_dir / f"_{chapter_path.stem}_concat.txt"
        with open(concat_list, 'w') as f:
            for tf in temp_files:
                f.write(f"file '{tf.name}'\n")
        
        import subprocess
        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', str(concat_list), '-c', 'copy', str(output_path)
        ], capture_output=True)
        
        # Cleanup temp files
        for tf in temp_files:
            tf.unlink()
        concat_list.unlink()
    
    print(f"    [DONE] {output_name}")
    return output_path

def get_chapter_number(filename):
    """Extract chapter number for sorting."""
    match = re.match(r'(\d+)', Path(filename).stem)
    return int(match.group(1)) if match else 999

def main():
    parser = argparse.ArgumentParser(description='Generate audiobook from chapter files')
    parser.add_argument('--input', '-i', default='./Kapitel', 
                       help='Input directory with chapter text files')
    parser.add_argument('--output', '-o', default='audio', 
                       help='Output directory for audio files')
    parser.add_argument('--voice', '-v', default=DEFAULT_VOICE,
                       choices=list(GERMAN_VOICES.keys()),
                       help=f'Voice to use (default: {DEFAULT_VOICE})')
    parser.add_argument('--start', '-s', type=int, default=0,
                       help='Start from chapter number')
    parser.add_argument('--end', '-e', type=int, default=999,
                       help='End at chapter number')
    parser.add_argument('--list-voices', action='store_true',
                       help='List available voices and exit')
    
    args = parser.parse_args()
    
    if args.list_voices:
        print("\nAvailable German voices:")
        for name, voice_id in GERMAN_VOICES.items():
            print(f"  {name}: {voice_id}")
        return
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' not found")
        return
    
    # Get all chapter files
    chapters = sorted(
        [f for f in input_dir.glob('*.txt')],
        key=lambda x: get_chapter_number(x.name)
    )
    
    print(f"\n{'='*60}")
    print(f"AUDIOBOOK GENERATOR")
    print(f"{'='*60}")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Voice: {args.voice} ({GERMAN_VOICES[args.voice]})")
    print(f"Chapters found: {len(chapters)}")
    print(f"{'='*60}\n")
    
    # Process chapters
    generated_files = []
    for chapter in chapters:
        ch_num = get_chapter_number(chapter.name)
        
        if ch_num < args.start or ch_num > args.end:
            continue
        
        print(f"\n[{ch_num:02d}] {chapter.name}")
        result = process_chapter(chapter, output_dir, args.voice)
        if result:
            generated_files.append(result)
    
    print(f"\n{'='*60}")
    print(f"COMPLETED: {len(generated_files)} audio files generated")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
