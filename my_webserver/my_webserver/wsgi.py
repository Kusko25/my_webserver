"""
WSGI config for my_webserver project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import logging
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_webserver.settings")

## Set up logging for debugging
# logging.basicConfig(
#     filename=R'J:\Workspaces\git\my_webserver\my_webserver\webserver.log',
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )

application = get_wsgi_application()
