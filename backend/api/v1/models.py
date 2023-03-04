from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models.constraints import UniqueConstraint


class Cart(models.Model):
    recipe = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='carts',
        to='Recipe',
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='carts',
        to=settings.AUTH_USER_MODEL,
        verbose_name='Пользователь'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='Этот рецепт уже добавлен в корзину.'
            )
        ]
        ordering = ('-id',)
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f'Корзина {self.user}: {self.recipe}'


class Favorite(models.Model):
    recipe = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='favorites',
        to='Recipe',
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='favorites',
        to=settings.AUTH_USER_MODEL,
        verbose_name='Пользователь'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='Этот рецепт уже добавлен в избранное.'
            )
        ]
        ordering = ('-id',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        return f'Избранное {self.user}: {self.recipe}'


class Ingredient(models.Model):
    measurement_unit = models.CharField(
        max_length=settings.MAX_CHARFIELD_LENGTH,
        verbose_name='Единицы измерения'
    )
    name = models.CharField(
        db_index=True,
        max_length=settings.MAX_CHARFIELD_LENGTH,
        verbose_name='Название ингредиента'
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('measurement_unit', 'name'),
                name='Такой ингредиент уже существует.'
            )
        ]
        ordering = ('-id',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    amount = models.PositiveIntegerField(
        validators=(
            MinValueValidator(
                limit_value=1,
                message='Должна быть хотя бы единица ингредиента.'
            ),
        ),
        verbose_name='Количество'
    )
    ingredient = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='ingredient_amount',
        to='Ingredient',
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='ingredient_amount',
        to='Recipe',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='Этот ингредиент уже добавлен в рецепт.'
            )
        ]
        ordering = ('-id',)
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количества ингредиентов'

    def __str__(self):
        return self.ingredient.measurement_unit


class Recipe(models.Model):
    author = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='recipes',
        to=settings.AUTH_USER_MODEL,
        verbose_name='Автор рецепта'
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(
                limit_value=settings.MIN_COOKING_TIME,
                message='Время приготовления не может составлять '
                        + 'менее 1 минуты.'
            ),
        ),
        verbose_name='Время приготовления (мин)'
    )
    image = models.ImageField(
        upload_to='recipes/%d/%m/%Y/',
        verbose_name='Изображение'
    )
    ingredients = models.ManyToManyField(
        related_name='recipes',
        through=IngredientAmount,
        through_fields=('recipe', 'ingredient'),
        to='Ingredient',
        verbose_name='Ингредиенты'
    )
    name = models.CharField(
        max_length=settings.MAX_CHARFIELD_LENGTH,
        verbose_name='Название рецепта'
    )
    tags = models.ManyToManyField(
        related_name='recipes',
        to='Tag',
        verbose_name='Теги'
    )
    text = models.TextField(
        verbose_name='Описание'
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    color = models.CharField(
        blank=True,
        default=None,
        max_length=settings.COLORFIELD_LENGTH,
        null=True,
        unique=True,
        validators=(
            RegexValidator(regex=r'^#([A-Fa-f0-9]{6})$'),
        ),
        verbose_name='Цвет (hex)'
    )
    name = models.CharField(
        max_length=settings.MAX_CHARFIELD_LENGTH,
        unique=True,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        blank=True,
        max_length=settings.MAX_CHARFIELD_LENGTH,
        null=True,
        unique=True,
        verbose_name='Слаг тега'
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name
