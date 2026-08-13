from django.contrib import admin
from .models import CustomUser
# Register your models here.
admin.site.register(CustomUser)

admin.site.site_header = "Instagram Admin Panel"
admin.site.site_title = "Instagram Portal"
admin.site.index_title = "Welcome to the Instagram"
