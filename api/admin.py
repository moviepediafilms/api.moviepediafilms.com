from django.contrib import admin

# Register your models here.
from api.models import Profile, Role


class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "city", "mobile", "gender", "dob", "rank", "mcoins"]


class RoleAdmin(admin.ModelAdmin):
    list_display = ["name"]


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Role, RoleAdmin)
