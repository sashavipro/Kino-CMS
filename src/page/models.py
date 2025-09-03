# from django.db import models
#
# from src.core.models import SeoBlock
#
#
# # PAGE ----------------------------------------------------------------------------------------
# class NewsPromotionPage(models.Model):
#     name = models.CharField(max_length=100)
#     date = models.DateField()
#     url = models.URLField()
#     active = models.BooleanField(default=True)
#
#     def __str__(self):
#         return self.name
#
#
# class MainPage(models.Model):
#     phone1 = models.CharField(max_length=11)
#     phone2 = models.CharField(max_length=11)
#     seo_text = models.TextField()
#     seo_block = models.ForeignKey(SeoBlock, on_delete=models.CASCADE, null=True, blank=True)
#
#     def __str__(self):
#         return f"Main Page ({self.phone1})"
#
#
# class Contact(models.Model):
#     name = models.CharField(max_length=50)
#     address = models.TextField()
#     coords = models.CharField(max_length=20)
#     logo = models.ImageField(upload_to="contacts/")
#     seo_block = models.ForeignKey(SeoBlock, on_delete=models.CASCADE, null=True, blank=True)
#
#     def __str__(self):
#         return self.name
#
#
# class OtherPage(models.Model):
#     name = models.CharField(max_length=50)
#     description = models.TextField()
#     main_image = models.ImageField(upload_to="pages/")
#     seo_block = models.ForeignKey(SeoBlock, on_delete=models.CASCADE, null=True, blank=True)
#
#     def __str__(self):
#         return self.name
