from django.contrib import admin
from schedule.models import TrackedTeam, Game


admin.site.register(Game)
admin.site.register(TrackedTeam)
