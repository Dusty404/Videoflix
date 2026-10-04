from django.urls import path
from .views import VideoListView, SingleVideoView, SingleVideoSegmentView



urlpatterns = [
    path('video/', VideoListView.as_view(), name='videolist'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', SingleVideoView.as_view(), name='single_video'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>', SingleVideoSegmentView.as_view(), name='single_video_segment')
]