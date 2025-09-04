from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re

class SeoValidator:  # Validator for Seo model
    @staticmethod
    def validate_keywords(value):  # Check cannot be None
        keywords = value.split(',')
        if not any(keywords):
            raise ValidationError(_('At least one keyword is required.'))

class ImageValidatorMixin:  # Universal Photo Validator
    @staticmethod
    def validate_file_extension(value):  # Valid extension Image
        allowed_extensions = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")
        if value:
            file_extension = value.name.rstrip('.')
            if not file_extension.endswith(allowed_extensions):
                raise ValidationError(_('Unsupported file format. Please upload a JPEG or PNG image.'))

    @staticmethod
    def validate_file_size(value):  # Valid size Image
        max_size = 15 * 1024 * 1024  # 15MB
        if value:
            if value.size > max_size:
                raise ValidationError(_('The image size exceeds the maximum allowed size of 15MB.'))


class UrlValidatorMixin:  # Universal URL Validator
    @staticmethod
    def validate_url(value):  # Check matching pattern
        url_pattern = r'^https?://(?:www\.)?[^\s/$.?#].[^\s]*$'
        if value:
            if not re.match(url_pattern, value):
                raise ValidationError(_('Invalid URL format.'))


class CounterValidatorMixin:  # Universal Counter Validator
    @staticmethod
    def count_integer(value):  # Check cannot be zero or negative
        if value:
            if value <= 0:
                raise ValidationError(_('The field cannot be zero or negative.'))