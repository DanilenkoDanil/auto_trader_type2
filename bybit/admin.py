from django.contrib import admin

from .models import Trader, Settings, Chat, EntryPrice, ErrorLog, GlobalSetting


@admin.register(ErrorLog)
class ErrorAdmin(admin.ModelAdmin):
    list_display = ('symbol','timestamp',)


admin.site.register(Trader)
admin.site.register(Settings)
admin.site.register(Chat)
admin.site.register(EntryPrice)
admin.site.register(GlobalSetting)
