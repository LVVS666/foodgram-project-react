from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Default UserManager with extra required arguments for creating user."""
    def _create_user(self, email, password, first_name,
                     last_name, username, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError('Email must be provided')
        if not first_name:
            raise ValueError('First name must be provided')
        if not last_name:
            raise ValueError('Last name must be provided')
        if not password:
            raise ValueError('Password must be provided')
        if not username:
            raise ValueError('Username must be provided')

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            username=username,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, email, password, first_name, last_name, username,
                    **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        return self._create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            username=username,
            **extra_fields
        )

    def create_superuser(self, email, password, first_name, last_name,
                         username, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
            username=username,
            **extra_fields
        )
