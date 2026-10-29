from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    name = 'video_app'

    def ready(self):
            """
            Import signal handlers when Django initializes the video application.
            """
            from . import signals