from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework.fields import ReadOnlyField
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.validators import UniqueTogetherValidator, ValidationError
from users.models import Follow

from .fields import Base64ImageField
from .mixins import CartFavoriteFlagsMixin
from .models import Ingredient, IngredientAmount, Recipe, Tag

User = get_user_model()


class UserSerializer(BaseUserSerializer):
    """
    Serializer for User instance. Also used as nested serializer at Recipe's
    serializer (read and create).
    All fields excluding "is_subscribed" are required for deserializing.
    """
    is_subscribed = SerializerMethodField()

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )
        model = User

    def get_is_subscribed(self, obj):
        """
        Is request's user subcribed to requested user?
        Anonymous user has no subscriptions and user has no subscription to
        himself.
        """
        request_user = self.context.get('request').user
        if request_user.is_anonymous or request_user == obj:
            return False

        return Follow.objects.filter(author=obj, user=request_user).exists()


class IngredientAmountSerializer(ModelSerializer):
    """
    Serializer for IngredientAmount instance. Used only for serializing as
    nested serializer at ReadRecipeSerializer.
    """
    id = ReadOnlyField(source='ingredient.id')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')
    name = ReadOnlyField(source='ingredient.name')

    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )
        model = IngredientAmount
        validators = [
            UniqueTogetherValidator(
                fields=('ingredient', 'recipe'),
                queryset=IngredientAmount.objects.all()
            )
        ]


class TagSerializer(ModelSerializer):
    """
    Serializer for Tag instance. Used only for serializing. Also used as
    nested serializer at Recipe's serializer (read and create).
    """
    class Meta:
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )
        model = Tag


class CreateRecipeSerializer(ModelSerializer, CartFavoriteFlagsMixin):
    """
    Serializer for creating Recipe instance. Used only for deserializing.
    Not required fields (used as Response additional data):
      * author
      * id
      * is_favorited
      * is_in_shopping_cart

    Despite the fact that the "ingredients" and "tags" are read-only (and not
    required, respectively), they are have to be passed while POST or may
    be passed while PATCH. This happens because this fields related as M:N
    with through model IngredientAmount, so saving is processing manually
    (custom validation is checking they're passed and passed correctly).

    Validated data never contains "ingredients" or "tags", because this
    validating manually (without adding to "validated_data"), so access to
    passed info through "initial_data".
    """
    author = UserSerializer(read_only=True)
    id = ReadOnlyField()
    image = Base64ImageField()
    ingredients = IngredientAmountSerializer(
        many=True,
        source='ingredient_amount',  # Related name Recipe --> IngredienAmount
        read_only=True
    )
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        model = Recipe

    @transaction.atomic
    def create(self, validated_data):
        """
        Create recipe instance.

        Inasmuch "tags" is M:N field without through
        model it should be set automatically using "set" method.

        Transaction used for full saving instances: if something will go
        wrong (e.g. recipe was created, but ingredients were not) roll-back
        mechanism will cancel all previous operations completely.
        """
        ingredients = self.initial_data.get('ingredients')
        tags = self.initial_data.get('tags')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredient_amount(objs=ingredients, recipe=recipe)

        return recipe

    def create_ingredient_amount(self, objs, recipe):
        """Create IngredientAmount (through model) entries manually."""
        IngredientAmount.objects.bulk_create(
            IngredientAmount(
                amount=int(ingrd['amount']),
                ingredient_id=int(ingrd['id']),
                recipe=recipe
            ) for ingrd in objs
        )

    def update(self, obj, validated_data):
        """
        Update (PATCH only) recipe instance.

        Inasmuch "tags" is M:N field
        without through model it should be cleared and set automatically
        using "set" and "clear" methods.

        Inasmuch "ingredients" is M:N field with through model it should be
        cleared and set manually.
        """
        ingredients = self.initial_data.get('ingredients')
        if ingredients is not None:
            IngredientAmount.objects.filter(recipe=obj).delete()
            self.create_ingredient_amount(objs=ingredients, recipe=obj)

        tags = self.initial_data.get('tags')
        if tags is not None:
            obj.tags.clear()
            obj.tags.set(tags)

        obj.cooking_time = validated_data.get('cooking_time', obj.cooking_time)
        obj.image = validated_data.get('image', obj.image)
        obj.name = validated_data.get('name', obj.name)
        obj.text = validated_data.get('text', obj.text)

        obj.save()

        return obj

    def validate(self, data):
        """
        Validate POST and PATCH request.

        If request body is empty (while PATCH) or not contains "tags" and
        "ingredients" (while POST) returns HTTP_400.

        If request body contains "ingredients" or "tags" calles additional
        validation functions.
        """
        initial_data = self.initial_data
        request = self.context['request']
        data['author'] = request.user

        if not request.data:
            raise ValidationError(
                detail={'errors': 'Пустой запрос, не надо дергать БД :('}
            )

        if request.method == 'POST':
            for field in ('tags', 'ingredients'):
                if initial_data.get(field) is None:
                    raise ValidationError(
                        detail={
                            f'{field}': 'Поле не может быть пустым.'
                        }
                    )

        if ingredients := initial_data.get('ingredients'):
            self._validate_ingredients(
                ingredients=ingredients
            )
        if tags := initial_data.get('tags'):
            self._validate_tags(
                tags=tags
            )

        return data

    def _validate_ingredients(self, ingredients: list[dict]):
        """
        Validate "ingredients" field.

        It must be list of unique dictionaries with "id" and "amount", like:
          [
            {
                "id": 9,
                "amount": 15
            },
            {
                "id": 14,
                "amount": 200
            },
            ...
          ]

        If needed "ingredient" doesn't exist returns HTTP_404.
        If any mismatch - returns HTTP_400.
        """
        if not isinstance(ingredients, list):
            raise ValidationError(
                detail={
                    'ingredients': 'Ожидался список.'
                }
            )

        if len(ingredients) == 0:
            raise ValidationError(
                detail={
                    'Рецепт должен иметь как минимум 1 ингредиент.'
                }
            )

        used_ingredients = []
        for item in ingredients:
            if not isinstance(item, dict):
                raise ValidationError(
                    detail={
                        'ingredients': 'Ожидались словари в списке.'
                    }
                )

            for key in ('id', 'amount'):
                if key not in item:
                    raise ValidationError(
                        detail={
                            'ingredients': f'Укажите {key} ингредиента.'
                        }
                    )

            ingredient = get_object_or_404(
                klass=Ingredient,
                pk=int(item['id'])
            )
            if ingredient in used_ingredients:
                raise ValidationError(
                    detail={
                        'ingredients': f'{ingredient} не может повторяться.'
                    }
                )

            if int(item['amount']) < 1:
                raise ValidationError(
                    detail={
                        'ingredients': f'{ingredient}: неверное количество.'
                    }
                )

            used_ingredients.append(ingredient)

        return ingredients

    def _validate_tags(self, tags):
        """
        Validate "tags" field.

        It must be list of unique integers (tag's ids), like:
          [
            1,
            2,
            ...
          ]

        If needed "tag" doesn't exist returns HTTP_404.
        If any mismatch - returns HTTP_400.
        """
        if not isinstance(tags, list):
            raise ValidationError(
                detail={
                    'tags': 'Ожидался список тегов.'
                }
            )

        if len(tags) == 0:
            raise ValidationError(
                detail={
                    'tags': 'Рецепт должен иметь как минимум 1 тег.'
                }
            )

        used_tags = []
        for id in tags:
            if not isinstance(id, int):
                raise ValidationError(
                    detail={
                        'tags': 'Ожидались id тегов.'
                    }
                )

            tag = get_object_or_404(klass=Tag, pk=id)
            if tag in used_tags:
                raise ValidationError(
                    detail={
                        'tag': f'{tag} не может повторяться.'
                    }
                )

            used_tags.append(tag)

        return tags


class FollowSerializer(ModelSerializer):
    """
    Serializer for Follow instance. Used only for serializing for Response data
    to "subscribe" and "subscriptions" action.
    """
    email = ReadOnlyField(source='author.email')
    first_name = ReadOnlyField(source='author.first_name')
    id = ReadOnlyField(source='author.id')
    is_subscribed = SerializerMethodField()
    last_name = ReadOnlyField(source='author.last_name')
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()
    username = ReadOnlyField(source='author.username')

    class Meta:
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )
        model = Follow

    def get_is_subscribed(self, obj):
        """Used only for existing instance, so follow exists."""
        return True

    def get_recipes(self, obj):
        """
        Get author's recipes (the user request's user subscribed to).
        Allows to get paginated response (limit count of recipes to be shown)
        using "recipes_limit" query param (e.g. ../?recipes_limit=4/).

        Returns data from RecipeMinifiedSerializer, that serialized limited
        queryset.
        """
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit'
        )
        recipes = Recipe.objects.filter(author=obj.author)
        if recipes_limit:
            if not recipes_limit.isdigit() or recipes_limit == '0':
                raise ValidationError(
                    detail={
                        'recipes_limit': 'Допустимо только натуральное число.'
                    }
                )
            recipes = recipes[:int(recipes_limit)]

        return RecipeMinifiedSerializer(instance=recipes, many=True).data

    def get_recipes_count(self, obj):
        """
        Get count of author's recipes (the user request's user subscribed to).
        """
        return Recipe.objects.filter(author=obj.author).count()


class IngredientSerializer(ModelSerializer):
    """
    Serializer for Ingredient instance. Used only for serializing.
    """
    class Meta:
        fields = (
            'id',
            'name',
            'measurement_unit'
        )
        model = Ingredient


class ReadRecipeSerializer(ModelSerializer, CartFavoriteFlagsMixin):
    """
    Serializer for reading Recipe instance. Used only for serializing.
    """
    author = UserSerializer()
    ingredients = IngredientAmountSerializer(
        many=True,
        source='ingredient_amount'  # Related name Recipe --> IngredienAmount
    )
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    tags = TagSerializer(many=True)

    class Meta:
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        model = Recipe
        read_only_fields = fields


class RecipeMinifiedSerializer(ModelSerializer):
    """
    Serializer for Recipe instance with limited data. Used only for
    serializing.
    """
    image = Base64ImageField()

    class Meta:
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        model = Recipe
        read_only_fields = fields
