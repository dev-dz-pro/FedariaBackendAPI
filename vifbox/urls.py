from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="Vifbox API",
      default_version='v1',
      description="Vifbox Api V1 Docemuntation",
      terms_of_service="https://www.vifbox.com/policies/terms/",
      contact=openapi.Contact(email="info@vifbox.com"),
      license=openapi.License(name="VIFBOX License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)



urlpatterns = [
    path('api/admin/', admin.site.urls),
    path('api/v1/', include('vifApp.urls')),
    path('api/v1/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui')
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
