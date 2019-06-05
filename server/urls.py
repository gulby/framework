from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from django.conf import settings
from django.views.static import serve

# framework
urlpatterns = [path("api/admin/", admin.site.urls), url(r"^front/human/", include("human.urls"))]

# server
urlpatterns += []

# for development
if settings.DEBUG:
    import debug_toolbar
    from .views import timeout, spin

    urlpatterns += [
        url(r"^__debug__/", include(debug_toolbar.urls)),
        url(r"^api/timeout/$", timeout, name="timeout"),
        url(r"^api/spin/$", spin, name="timeout"),
        url(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
        url(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    ]
