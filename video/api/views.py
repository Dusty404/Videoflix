from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Video
from.serializers import VideoListSerializer

class VideoListView(generics.ListAPIView):
    model = Video
    serializer_class = VideoListSerializer
    queryset = Video.objects.all()