from django.contrib import admin

# Register your models here.
from api.models import Profile, Role, Order, Movie, MovieGenre, MovieLanguage


class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "city", "mobile", "gender", "dob", "rank", "mcoins"]


class RoleAdmin(admin.ModelAdmin):
    list_display = ["name"]


class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_id", "payment_id"]


class MovieAdmin(admin.ModelAdmin):
    list_display = ["title", "state", "link"]


class MovieGenreAdmin(admin.ModelAdmin):
    list_display = ["name"]


class MovieLanguageAdmin(admin.ModelAdmin):
    list_display = ["name"]


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Movie, MovieAdmin)
admin.site.register(MovieGenre, MovieGenreAdmin)
admin.site.register(MovieLanguage, MovieLanguageAdmin)
