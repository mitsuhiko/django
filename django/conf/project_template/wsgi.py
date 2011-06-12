from django.core.handlers import WSGIHandler


# You can wrap the application object here to apply WSGI middlewares.
# The `application` object here is used by both the local runserver
# command as well as a properly configured WSGI server.
application = WSGIHandler()

# Example middleware:
# from werkzeug.debug import DebuggedApplication
# application = DebuggedApplication(application)
