from django.contrib import admin
from finder.models import (
    RecruitmentApplication, 
    RecruitmentPost,
    TeamInvitation
)


admin.site.register(RecruitmentApplication)
admin.site.register(RecruitmentPost)
admin.site.register(TeamInvitation)
