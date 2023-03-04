import base64

from django.core.files.base import ContentFile
from rest_framework.fields import ImageField


class Base64ImageField(ImageField):
    """
    Field to save file encoded in base64. Returns url to file at media dir.
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)
