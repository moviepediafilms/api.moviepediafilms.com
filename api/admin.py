from django.contrib import admin
from django.contrib.auth.models import User
from import_export.admin import ExportMixin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from api.models import (
    Profile,
    Role,
    Order,
    Movie,
    Genre,
    MpGenre,
    MovieLanguage,
    MovieRateReview,
    MovieList,
    Package,
    PackageAttribute,
    Release,
    CrewMember,
    CrewMemberRequest,
    ContestType,
    Contest,
    Notification,
)

# Deregister default admin classes
admin.site.unregister(User)


@admin.register(Profile)
class ProfileAdmin(ExportMixin, admin.ModelAdmin):
    search_fields = ["user__first_name", "user__last_name", "user__username", "city"]
    exclude = ["follows"]
    list_display = [
        "user",
        "city",
        "mobile",
        "gender",
        "dob",
        "curator_rank",
        "creator_rank",
        "mcoins",
    ]
    list_filter = ["is_celeb", "gender"]


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(Order)
class OrderAdmin(ExportMixin, admin.ModelAdmin):
    search_fields = [
        "owner__first_name",
        "owner__last_name",
        "owner__email",
        "order_id",
        "payment_id",
    ]
    list_display = ["owner", "order_id", "payment_id"]
    readonly_fields = ["movies"]


@admin.register(Movie)
class MovieAdmin(ExportMixin, admin.ModelAdmin):
    search_fields = ["title", "link"]
    list_filter = [
        "orders__package",
        "state",
        "approved",
        "created_at",
    ]
    list_display = [
        "orders",
        "title",
        "state",
        "link",
        "approved",
        "is_paid",
        "created_at",
        "director",
        "director_name",
        "submitted_by",
        "jury_rating",
        "audience_rating",
        "poster",
    ]
    ordering = ["-created_at", "title"]
    readonly_fields = ["poster", "publish_on"]
    filter_horizontal = ["contests"]

    def submitted_by(self, movie):
        order = movie.orders.first()
        return order and order.owner

    def director(self, movie):
        director = movie.crewmember_set.filter(role__name="Director").first()
        if director:
            return director.profile.user

    def director_name(self, movie):
        return movie.crewmember_set.get(
            role__name="Director"
        ).profile.user.get_full_name()

    def is_paid(self, movie):
        return movie.orders.exclude(payment_id=None).exists()


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(MpGenre)
class MpGenreAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(MovieLanguage)
class MovieLanguageAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(MovieRateReview)
class MovieRateReviewAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ["id", "author", "content", "movie", "published_at", "rating"]


@admin.register(MovieList)
class MovieListAdmin(ExportMixin, admin.ModelAdmin):
    search_fields = ["owner__email", "owner__first_name", "owner__last_name", "name"]
    list_display = ["name", "owner", "contest", "frozen"]
    list_filter = ["contest"]

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == "movies":
            field.queryset = Movie.objects.all().order_by("title")
        return field


class AttributesInPackage(ExportMixin, admin.TabularInline):
    model = Package.attributes.through


@admin.register(Release)
class ReleaseHistoryAdmin(admin.ModelAdmin):
    search_fields = ["movie__title", "contest__name"]
    list_filter = ["contest", "on"]
    list_display = ["movie", "contest", "on"]


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ["name", "amount"]
    inlines = [AttributesInPackage]


@admin.register(PackageAttribute)
class PackageAttributeAdmin(admin.ModelAdmin):
    list_display = ["name"]


@admin.register(CrewMember)
class CrewMemberAdmin(ExportMixin, admin.ModelAdmin):
    search_fields = ["profile__user__email", "movie__title"]
    list_filter = ["role"]
    list_display = [
        "user",
        "movie",
        "role",
    ]

    def user(self, membership):
        return membership.profile.user.email


@admin.register(CrewMemberRequest)
class CrewMemberRequestAdmin(ExportMixin, admin.ModelAdmin):
    search_fields = ["user__email", "movie__title"]
    list_filter = ["role", "state"]
    list_display = ["requestor", "movie", "user", "role", "state", "reason"]


@admin.register(ContestType)
class ContestTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]


class MoviesInContest(ExportMixin, admin.TabularInline):
    model = Contest.movies.through


@admin.register(Contest)
class ContestAdmin(ExportMixin, admin.ModelAdmin):
    list_display = [
        "name",
        "start",
        "end",
        "days_per_movie",
        "state",
    ]
    inlines = [
        MoviesInContest,
    ]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["title", "profile", "content"]


@admin.register(User)
class UserAdmin(ExportMixin, BaseUserAdmin):
    pass
