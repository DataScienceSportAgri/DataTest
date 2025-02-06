from django.contrib import admin
from django import forms
from django.utils.html import format_html

from .models import ClassementBubble, Bubble, ColorPreset


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



@admin.register(ClassementBubble)
class ClassementBubbleAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color_start', 'color_end', 'is_public')
    list_filter = ('is_public', 'created_at')
    autocomplete_fields = ('color_start', 'color_end')