from django.contrib import admin

# Register your models here.
from display.models import Contest, Track, Aeroplane, Team, Contestant


class ContestantInline(admin.TabularInline):
    model = Contestant


class ContestAdmin(admin.ModelAdmin):
    inlines = (
        ContestantInline,
    )


admin.site.register(Contest, ContestAdmin)
admin.site.register(Track)
admin.site.register(Aeroplane)
admin.site.register(Team)
admin.site.register(Contestant)
