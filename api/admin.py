from django.contrib import admin
from django.db.models import Count

# Register your models here.
from api.models import (
    Profile,
    Role,
    Order,
    Movie,
    MovieGenre,
    MovieLanguage,
    MovieRateReview,
    MovieList,
    Package,
    CrewMember,
    CrewMemberRequest,
    ContestType,
    Contest,
)


class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "city", "mobile", "gender", "dob", "rank", "mcoins"]
    list_filter = ["is_celeb", "gender"]


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


class MovieRateReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "author", "content", "movie", "published_at", "rating"]


class MovieListAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "contest", "frozen"]
    list_filter = ["owner", "contest"]


class PackageAdmin(admin.ModelAdmin):
    list_display = [
        "name",
    ]


class CrewMemberAdmin(admin.ModelAdmin):
    search_fields = ["profile__user__email", "movie__title"]
    list_filter = ["role"]
    list_display = [
        "user",
        "movie",
        "role",
    ]

    def user(self, membership):
        return membership.profile.user.email


class CrewMemberRequestAdmin(admin.ModelAdmin):
    search_fields = ["user__user__email", "movie__title"]
    list_filter = ["role", "state"]
    list_display = ["requestor", "movie", "user", "role", "state", "reason"]


class ContestTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]


class ContestAdmin(admin.ModelAdmin):
    list_display = ["name", "start", "end", "days_per_movie", "state"]


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Movie, MovieAdmin)
admin.site.register(MovieGenre, MovieGenreAdmin)
admin.site.register(MovieLanguage, MovieLanguageAdmin)
admin.site.register(MovieRateReview, MovieRateReviewAdmin)
admin.site.register(Package, PackageAdmin)
admin.site.register(MovieList, MovieListAdmin)
admin.site.register(CrewMember, CrewMemberAdmin)
admin.site.register(CrewMemberRequest, CrewMemberRequestAdmin)
admin.site.register(ContestType, ContestTypeAdmin)
admin.site.register(Contest, ContestAdmin)
