from django.contrib.auth import get_user_model
from django.db.models import F, QuerySet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from djoser import utils
from djoser.conf import settings as djoser_settings
from djoser.views import TokenCreateView as BaseTokenCreateView
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST)
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from users.models import Follow

from .filters import IngredientSearchFilter, RecipeFilter
from .models import Cart, Favorite, Ingredient, IngredientAmount, Recipe, Tag
from .paginations import PageLimitPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (CreateRecipeSerializer, FollowSerializer,
                          IngredientSerializer, ReadRecipeSerializer,
                          RecipeMinifiedSerializer, TagSerializer)

User = get_user_model()


class IngredientViewSet(ReadOnlyModelViewSet):
    filter_backends = (IngredientSearchFilter,)
    pagination_class = None
    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    search_fields = ('^name',)
    serializer_class = IngredientSerializer


class RecipeViewSet(ModelViewSet):
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsOwnerOrReadOnly,)
    queryset = Recipe.objects.all()

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """
        Endpoint to download shopping list (generated using recipes from cart).
        Works with 1 instance, but detail=False means that DRF should't create
        route with ../{id}/.

        "ingredients" has structure as:
          [
            {
              'amount': 10,
              'name': 'овощи',
              'units': 'г'
            },
            {
              'amount': 15,
              'name': 'сахар',
              'units': 'г'
            },
            ...
          ]
        If cart is empty returns HTTP_400.

        Returns shop_list.txt file with ingredients to buy.
        """
        ingredients: QuerySet[dict] = IngredientAmount.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'amount',
            name=F('ingredient__name'),
            units=F('ingredient__measurement_unit')
        )
        result = {}

        for ingrd_dict in ingredients:
            if (ingredient := ingrd_dict['name']) not in result:
                result[ingredient] = {
                    'amount': ingrd_dict['amount'],
                    'units': ingrd_dict['units']
                }
            else:
                result[ingredient]['amount'] += ingrd_dict['amount']

        if not result:
            return Response(
                data={
                    'errors': 'Корзина пуста.'
                },
                status=HTTP_400_BAD_REQUEST
            )

        shopping_list = ['Список ингредиентов к покупке:']
        for key, value in result.items():
            key = key[0].upper() + key[1:]
            amount = value['amount']
            units = value['units']
            shopping_list.append(f'\n* {key} ({units}) — {amount}')

        shopping_list = ''.join(shopping_list)
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=shop_list.txt'

        return response

    @action(detail=True, methods=['DELETE', 'POST'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        """
        Endpoint to DELETE or POST 1 recipe at favorites.
        """
        return self._obj_operation(
            model=Favorite,
            recipe_pk=pk,
            request=request
        )

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReadRecipeSerializer

        return CreateRecipeSerializer

    @action(detail=True, methods=['DELETE', 'POST'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        """
        Endpoint to DELETE or POST 1 recipe at cart.
        """
        return self._obj_operation(
            model=Cart,
            recipe_pk=pk,
            request=request
        )

    def _create_object(self, model, request, recipe_pk):
        """
        Create Favorite or Cart entry with given recipe and request's user.

        If passed recipe doesn't exist returns HTTP_404.
        If object exists returns HTTP_400.

        Returns short view of added recipe with HTTP_201.
        """
        user = request.user
        obj = model.objects.filter(recipe__pk=recipe_pk, user=user)

        if obj.exists():
            return Response(
                data={
                    'errors': f'{model._meta.verbose_name}: рецепт уже'
                              + ' добавлен.'
                },
                status=HTTP_400_BAD_REQUEST
            )
        recipe = get_object_or_404(klass=Recipe, pk=recipe_pk)
        model.objects.create(recipe=recipe, user=user)

        return Response(
            data=RecipeMinifiedSerializer(instance=recipe).data,
            status=HTTP_201_CREATED
        )

    def _delete_object(self, model, request, recipe_pk):
        """
        Delete Favorite or Cart entry with given recipe and request's user.

        If passed recipe doesn't exist returns HTTP_404.
        If object exists returns HTTP_400.

        Returns HTTP_204.
        """
        user = request.user
        recipe = get_object_or_404(klass=Recipe, pk=recipe_pk)
        obj = model.objects.filter(recipe=recipe, user=user)

        if not obj.exists():
            return Response(
                data={
                    'errors': f'{model._meta.verbose_name}: рецепт не найден.'
                },
                status=HTTP_400_BAD_REQUEST
            )
        obj.delete()

        return Response(status=HTTP_204_NO_CONTENT)

    def _obj_operation(self, **kwargs):
        """Calles function according to request method."""
        if kwargs['request'].method == 'DELETE':
            return self._delete_object(**kwargs)

        return self._create_object(**kwargs)


class TagViewSet(ReadOnlyModelViewSet):
    pagination_class = None
    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class TokenCreateView(BaseTokenCreateView):
    """Default djoser view, but changed status from HTTP_200 to HTTP_201."""
    serializer_class = djoser_settings.SERIALIZERS.token_create
    permission_classes = djoser_settings.PERMISSIONS.token_create

    def _action(self, serializer):
        token = utils.login_user(request=self.request, user=serializer.user)
        token_serializer_class = djoser_settings.SERIALIZERS.token
        return Response(
            data=token_serializer_class(token).data, status=HTTP_201_CREATED
        )


class UserViewSet(BaseUserViewSet):
    pagination_class = PageLimitPagination

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        """
        Allow only GET method. Calles default djoser view.
        Works with 1 instance, but detail=False means that DRF should't create
        route with ../{id}/.
        """
        return super().me(request, *args, **kwargs)

    @action(detail=True, methods=['DELETE', 'POST'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        """
        Endpoint to subcribe to user. Request's user - who subscribing.

        If author doesn't exist return HTTP_404.
        If author and user are equal or subscription already exist (while POST)
        or subscription already doesn't exist (while DELETE) returns HTTP_400.

        Returns HTTP_204 (while DELETE) or HTTP_201 (while POST).
        """
        kwargs = {
            'author': get_object_or_404(klass=User, pk=id),
            'user': request.user
        }

        if kwargs['user'] == kwargs['author']:
            return Response(
                data={
                    'errors': 'Нельзя подписаться или отписаться от себя.'
                },
                status=HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if Follow.objects.filter(**kwargs).exists():
                return Response(
                    data={'errors': 'Подписка уже существует.'},
                    status=HTTP_400_BAD_REQUEST
                )

            subscription = Follow.objects.create(**kwargs)
            serializer = FollowSerializer(
                context={'request': request},
                instance=subscription
            )
            return Response(data=serializer.data, status=HTTP_201_CREATED)

        if (subscription := Follow.objects.filter(**kwargs)).exists():
            subscription.delete()
            return Response(status=HTTP_204_NO_CONTENT)

        return Response(
            data={'errors': 'Вы не подписаны на этого пользователя.'},
            status=HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        """
        Endpoint to get list of request's user subscriptions.

        Returns paginated (using parent ViewSet paginator) response.
        """
        subsriptions = Follow.objects.filter(user=request.user)
        paginated_queryset = self.paginate_queryset(subsriptions)
        serializer = FollowSerializer(
            context={'request': request},
            instance=paginated_queryset,
            many=True
        )

        return self.get_paginated_response(data=serializer.data)
