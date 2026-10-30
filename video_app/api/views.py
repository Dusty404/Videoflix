from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from .permissions import HasJWTPermission
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from pathlib import Path

from .serializers import VideoSerializer
from video_app.models import Video


class VideoListView(ListAPIView):
    permission_classes = [HasJWTPermission]

    queryset = Video.objects.all().order_by("id")
    serializer_class = VideoSerializer

class SingleVideoView(APIView):
    permission_classes = [HasJWTPermission]

    def get(self, request, movie_id, resolution):
        """
        Open and stream the requested video rendition's HLS playlist.

        Args:
            request (Request): The incoming HTTP request.
            movie_id (int): Primary key of the requested video.
            resolution (str): Requested rendition: 480p, 720p, or 1080p.

        Returns:
            FileResponse: Playlist with application/vnd.apple.mpegurl content type.

        Raises:
            Http404: If the video, allowed resolution, or playlist is unavailable.
            ValueError: If the video has no attached source file.
            OSError: If opening the playlist fails for another filesystem reason.
        """
        video = get_object_or_404(Video, pk=movie_id)
        source = Path(video.video_file.path)

        if resolution not in {"480p", "720p", "1080p"}:
            raise Http404("Auflösung nicht verfügbar.")

        source = Path(video.video_file.path)
        playlist_path = source.parent/resolution/"index.m3u8"

        try:
            file = playlist_path.open("rb")
        except FileNotFoundError:
            raise Http404("Playlist nicht verfügbar.")

        return FileResponse( file, content_type="application/vnd.apple.mpegurl")
    
class SingleVideoSegmentView(APIView):
    permission_classes = [HasJWTPermission]
    
    def get(self, request, movie_id, resolution, segment):
        """
        Open and stream a segment from the requested video rendition.

        Args:
            request (Request): The incoming HTTP request.
            movie_id (int): Primary key of the requested video.
            resolution (str): Requested rendition: 480p, 720p, or 1080p.
            segment (str): Segment filename from the URL, such as 000.ts.

        Returns:
            FileResponse: Segment with video/mp2t content type.

        Raises:
            Http404: If the video, allowed resolution, or segment is unavailable.
            ValueError: If source-path access occurs without an attached file.
            OSError: If opening the segment fails for another filesystem reason.
        """
        video = get_object_or_404(Video, pk=movie_id)
        source = Path(video.video_file.path)

        if resolution not in {"480p", "720p", "1080p"}:
            raise Http404("Auflösung nicht verfügbar.")

        if not video.video_file:
            raise Http404("Keine Videodatei vorhanden.")

        segment_path = source.parent / resolution / segment

        try:
            file = segment_path.open("rb")
        except FileNotFoundError:
            raise Http404("Segment nicht verfügbar.")

        return FileResponse(file, content_type="video/mp2t")