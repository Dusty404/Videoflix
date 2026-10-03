import subprocess
from pathlib import Path

def convert_480p(source):
    source = Path(source)
    target = source.with_name(f"{source.stem}_480p.mp4")
    subprocess.run(["ffmpeg", "-y", "-i", str(source), "-s", "hd480", "-c:v", "libx264", "-crf", "23", "-c:a", "aac", str(target)],check=True)

def convert_720p(source):
    source = Path(source)
    target = source.with_name(f"{source.stem}_720p.mp4")
    subprocess.run(["ffmpeg", "-y", "-i", str(source), "-s", "hd720", "-c:v", "libx264", "-crf", "23", "-c:a", "aac", str(target)],check=True)