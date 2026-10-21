import subprocess
from pathlib import Path


def convert_hls(source, resolution):
    """
    Run FFmpeg to generate an HLS playlist and segments beside the source.

    Create a resolution-specific directory and overwrite existing output.

    Args:
        source (str | Path): Filesystem path to the source video.
        resolution (str): Target resolution without p, such as 480, 720, or 1080.

    Returns:
        str: Filesystem path to the generated index.m3u8 playlist.

    Raises:
        subprocess.CalledProcessError: If FFmpeg exits unsuccessfully.
        OSError: If filesystem access or process creation fails.
    """
    source = Path(source)
    output_dir = source.parent / f"{resolution}p"
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
            str(output_dir / "%03d.ts"),
            "-f", "hls",
            str(playlist)
        ],check=True)
    return str(playlist)


def convert_480p(source):
    """
    Generate the 480p HLS rendition through the shared conversion helper.

    Args:
        source (str | Path): Filesystem path to the source video.

    Returns:
        str: Path to the generated playlist.

    Raises:
        subprocess.CalledProcessError: If FFmpeg conversion fails.
        OSError: If filesystem access or process creation fails.
    """
    return convert_hls(source, "480")


def convert_720p(source):
    """
    Generate the 720p HLS rendition through the shared conversion helper.

    Args:
        source (str | Path): Filesystem path to the source video.

    Returns:
        str: Path to the generated playlist.

    Raises:
        subprocess.CalledProcessError: If FFmpeg conversion fails.
        OSError: If filesystem access or process creation fails.
    """
    return convert_hls(source, "720")

def convert_1080p(source):
    """
    Generate the 1080p HLS rendition through the shared conversion helper.

    Args:
        source (str | Path): Filesystem path to the source video.

    Returns:
        str: Path to the generated playlist.

    Raises:
        subprocess.CalledProcessError: If FFmpeg conversion fails.
        OSError: If filesystem access or process creation fails.
    """
    return convert_hls(source, "1080")