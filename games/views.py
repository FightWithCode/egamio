from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Game
from accounts.models import Role
from rest_framework.response import Response


class ListGames(APIView):
    def get(self, request):
        response = {}
        try:
            data = []
            for game in Game.objects.all():
                temp_dict = {}
                temp_dict['id'] = game.id
                temp_dict['name'] = game.name
                data.append(temp_dict)
            response["msg"] = "fetched"
            response["data"] = data
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response["msg"] = "Something went wrong"
            response["error"] = str(e)
            response["data"] = None
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        

class ListRoles(APIView):
    def get(self, request, game: str):
        response = {}
        try:
            data = []
            for role in Role.objects.filter(game__name=game):
                temp_dict = {}
                temp_dict['id'] = role.id
                temp_dict['name'] = role.name
                data.append(temp_dict)
            response["msg"] = "fetched"
            response["data"] = data
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response["msg"] = "Something went wrong"
            response["error"] = str(e)
            response["data"] = None
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
