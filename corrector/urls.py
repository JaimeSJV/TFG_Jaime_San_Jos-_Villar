from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import cuad_image_view

urlpatterns = [
    path('', views.cuad_image_view, name='home'),
]

if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)