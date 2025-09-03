# from django.db import models
#
# # CINEMA ----------------------------------------------------------------------------------------
# class Film(models.Model):
#     title = models.CharField(max_length=100)
#     trailer_url = models.URLField()
#     is_2d = models.BooleanField(default=True)
#     is_3d = models.BooleanField(default=False)
#     is_imax = models.BooleanField(default=False)
#
#     def __str__(self):
#         return self.title
#
#
# class Hall(models.Model):
#     cinema = models.ForeignKey("Cinema", on_delete=models.CASCADE)
#     number = models.SmallIntegerField()
#     scheme_image = models.ImageField(upload_to="halls/")
#     banner_image = models.ImageField(upload_to="halls/")
#
#     def __str__(self):
#         return f"Hall {self.number} ({self.cinema})"
#
#
# class Cinema(models.Model):
#     name = models.CharField(max_length=100)
#     conditions = models.TextField()
#
#     def __str__(self):
#         return self.name
#
#
# class MovieSession(models.Model):
#     film = models.ForeignKey(Film, on_delete=models.CASCADE)
#     hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
#     price = models.SmallIntegerField()
#     time = models.TimeField()
#     is_3d = models.BooleanField(default=False)
#     is_dbox = models.BooleanField(default=False)
#     is_vip = models.BooleanField(default=False)
#
#     def __str__(self):
#         return f"{self.film} in {self.hall} at {self.time}"
