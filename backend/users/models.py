from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from .managers import UserManager


class Follow(models.Model):
    author = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='following',
        to=settings.AUTH_USER_MODEL,
        verbose_name='Автор'
    )
    user = models.ForeignKey(
        on_delete=models.CASCADE,
        related_name='follower',
        to=settings.AUTH_USER_MODEL,
        verbose_name='Подписчик'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'user',),
                name='Подписка уже существует.'
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F("user")),
                name='Подписка на самого себя не разрешена.'
            )
        ]
        ordering = ('author', 'user')
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'Подписка {self.user}: {self.author}'


class User(AbstractBaseUser, PermissionsMixin):
    """
    Default User model, but used custom manager, email as login field and
    custom set of required fields for registration.
    Also changed options of fields such as email and first_name length and
    others.
    """
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата регистрации'
    )
    email = models.EmailField(
        error_messages={
            'unique': 'Пользователь с такой почтой уже существует.',
        },
        max_length=settings.MAX_EMAIL_LENGTH,
        unique=True,
        verbose_name='Адрес электронной почты'
    )
    first_name = models.CharField(
        max_length=settings.MAX_NAMES_LENGTH,
        verbose_name='Имя'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активный'
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name='Модератор'
    )
    last_name = models.CharField(
        max_length=settings.MAX_NAMES_LENGTH,
        verbose_name='Фамилия'
    )
    password = models.CharField(
        max_length=settings.MAX_PASSWORD_LENGTH,
        verbose_name='Пароль'
    )
    username = models.CharField(
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
        },
        max_length=settings.MAX_NAMES_LENGTH,
        unique=True,
        validators=(
            UnicodeUsernameValidator(),
        ),
        verbose_name='Имя пользователя'
    )

    objects = UserManager()

    REQUIRED_FIELDS = ('first_name', 'last_name', 'password', 'username')
    USERNAME_FIELD = 'email'

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    def get_full_name(self):
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self):
        return self.first_name
