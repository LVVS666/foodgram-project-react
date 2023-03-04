from .models import Cart, Favorite


class CartFavoriteFlagsMixin:
    """
    Mixin for serializer provides add "is_favorite" and "is_in_shopping_cart"
    fields using SerializerMethodField.

    For anonymous user returns False, because he hasn't got favorite and cart
    list.
    For authenticated user uses Favorite or Cart model. If it has any instance
    with current Recipe and User that made request returns True, else False.
    """
    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False

        return Favorite.objects.filter(recipe=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False

        return Cart.objects.filter(recipe=obj, user=user).exists()
