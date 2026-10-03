import subprocess
from pathlib import Path


def convert_hls(source, resolution):
    source = Path(source)
    output_dir = source.parent / resolution
    output_dir.mkdir(parents=True, exist_ok=True)
    playlist = output_dir / "index.m3u8"
    subprocess.run([
            "ffmpeg",
            "-y",
            "-i", str(source),
            "-map", "0:v:0",
            "-map", "0:a:0?",
            "-s", f"hd{resolution}",
            "-c:v", "libx264",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-flags", "+cgop",
            "-force_key_frames", "expr:gte(t,n_forced*10)",
            "-c:a", "aac",
            "-start_number", "0",
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-hls_playlist_type", "vod",
            "-hls_segment_filename",
            str(output_dir / "segment_%03d.ts"),
            "-f", "hls",
            str(playlist)
        ],check=True)
    return str(playlist)


def convert_480p(source):
    return convert_hls(source, "480")


def convert_720p(source):
    return convert_hls(source, "720")