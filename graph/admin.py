from django.contrib import admin
from .models import ColorPreset
from django.utils.html import format_html
# Register your models here.
@admin.register(ColorPreset)
class ColorPresetAdmin(admin.ModelAdmin):
    search_fields = ['name', 'color_code']  # <-- Obligatoire pour autocomplete
    list_display = ('name', 'color_code', 'color_preview')
    readonly_fields = ('color_preview',)

    def color_preview(self, obj):
        return format_html(
            '<div style="width: 50px; height: 20px; background-color: {}"></div>',
            obj.color_code
        )

    color_preview.short_description = "Aperçu"