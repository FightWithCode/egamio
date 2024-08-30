from django.contrib import admin
from finder.models import (
    RecruitmentApplication, 
    RecruitmentPost, 
    PlayerRecruitmentPost, 
    TeamInvitation
)


admin.site.register(RecruitmentApplication)
admin.site.register(RecruitmentPost)
admin.site.register(PlayerRecruitmentPost)
admin.site.register(TeamInvitation)
