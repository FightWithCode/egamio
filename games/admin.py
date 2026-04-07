from django.contrib import admin

# models import 
from games.models import Game, GameTag

admin.site.register(Game)
admin.site.register(GameTag)
