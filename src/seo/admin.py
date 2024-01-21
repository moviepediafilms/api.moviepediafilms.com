from django.contrib import admin
from .models import Page, MetaValue
from import_export.admin import ExportMixin


@admin.register(Page)
class PageAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("url", "is_pattern", "model_pk", "models_to_select", "tags_count")
    list_filter = ("is_pattern", "models_to_select")
    search_fields = ("url",)

    def tags_count(self, obj):
        return len(obj.tags.split("\n")) if obj.tags else 0


@admin.register(MetaValue)
class MetaValueAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("name", "value")
    search_fields = ("name",)
