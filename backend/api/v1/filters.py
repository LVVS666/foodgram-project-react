from django.contrib.auth import get_user_model
from django_filters import (AllValuesMultipleFilter, ChoiceFilter, FilterSet,
                            ModelChoiceFilter)
from rest_framework.filters import SearchFilter

from .models import Recipe

User = get_user_model()

BOOLEAN_CHOICES = (
    (0, 'false',),
    (1, 'true',),
)


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(FilterSet):
    """
    Used by DjangoFilterBackends came from django-filter library.
    Allows to filter Recipe instance by:
      - author: ../?author=<author>/
                ../?author=1/
        One selection (id).

      - is_favorited: ../?is_favorited=<0_or_1>/
                      ../?is_favorited=0/
        One selection (false or true).

      - is_in_shopping_cart: ../?is_in_shopping_cart=<0_or_1>/
                             ../?is_in_shopping_cart=1/
        One selection (false or true).

      - tags: ../tags=<slug_1>&tags=<slug_2>&../
              ../tags=breakfast&tags=5_min&../
        Many selection using unique slug of tag.

    This filters may be combined.
    """
    author = ModelChoiceFilter(
        queryset=User.objects.all()
    )
    is_favorited = ChoiceFilter(
        choices=BOOLEAN_CHOICES,
        method='get_is_favorited'
    )
    is_in_shopping_cart = ChoiceFilter(
        choices=BOOLEAN_CHOICES,
        method='get_is_in_shopping_cart'
    )
    tags = AllValuesMultipleFilter(
        field_name='tags__slug'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags')

    def get_is_favorited(self, queryset, name, value):
        """
        Returns answer for question "is recipe in the user's favorites?".

        * For anonymous user with requested favorites returns empty QuerySet.
        * For anonymous user with requested not favorites returns source
          QuerySet (all recipes for anonymous are not favorite).
        * For authenticated user uses filter or exclude option with related
          entries at Favorite model.
        """
        user = self.request.user
        value = int(value)

        if user.is_anonymous:
            return Recipe.objects.none() if value else queryset

        if value:
            return queryset.filter(favorites__user=user)

        return queryset.exclude(favorites__user=user)

    def get_is_in_shopping_cart(self, queryset, name, value):
        """
        Returns answer for question "is recipe in the user's cart?".

        * For anonymous user with requested favorites returns empty QuerySet.
        * For anonymous user with requested not favorites returns source
          QuerySet (all recipes for anonymous are not favorite).
        * For authenticated user uses filter or exclude option with related
          entries at Cart model.
        """
        user = self.request.user
        value = int(value)

        if user.is_anonymous:
            return Recipe.objects.none() if value else queryset

        if value:
            return queryset.filter(carts__user=user)

        return queryset.exclude(carts__user=user)
