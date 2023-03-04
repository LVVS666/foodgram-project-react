from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                    TokenCreateView, UserViewSet)

app_name = 'api_v1'

router_v1 = DefaultRouter()

router_v1.register(prefix='ingredients', viewset=IngredientViewSet)
router_v1.register(prefix='recipes', viewset=RecipeViewSet)
router_v1.register(prefix='tags', viewset=TagViewSet)
router_v1.register(prefix='users', viewset=UserViewSet)

urlpatterns = [
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    re_path(r"^auth/token/login/?$", TokenCreateView.as_view(), name="login"),
    path('auth/', include('djoser.urls.authtoken')),
]
