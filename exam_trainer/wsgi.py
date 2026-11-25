"""WSGI config for exam_trainer project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "exam_trainer.settings")

application = get_wsgi_application()
