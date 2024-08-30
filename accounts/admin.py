from django.contrib import admin
from .models  import User, Role, Team, UserGameProfile, UserShort


admin.site.register(User)
admin.site.register(Team)
admin.site.register(Role)
admin.site.register(UserGameProfile),
admin.site.register(UserShort)
