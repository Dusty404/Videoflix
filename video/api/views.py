from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from .permissions import HasJWTPermission
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from .serializers import VideoSerializer
from ..models import Video
from pathlib import Path


class VideoListView(ListAPIView):
    permission_classes = [HasJWTPermission]

    queryset = Video.objects.all().order_by("id")
    serializer_class = VideoSerializer
    pagination_class = None

class SingleVideoView(APIView):
    permission_classes = [HasJWTPermission]

    def get(self, request, movie_id, resolution):
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