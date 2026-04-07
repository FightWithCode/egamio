from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Game, GameTag
from .serializers import GameTagSerializer
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


class PopularGameTags(APIView):
    def get(self, request):
        response = {}
        try:
            game_id = request.query_params.get('game_id')
            game_name = request.query_params.get('game')
            limit = request.query_params.get('limit', 15)
            try:
                limit = max(1, min(int(limit), 25))
            except (TypeError, ValueError):
                limit = 15

            if not game_id and not game_name:
                response["msg"] = "game_id or game is required"
                response["error"] = "missing_game_param"
                response["data"] = []
                return Response(response, status=status.HTTP_400_BAD_REQUEST)

            queryset = GameTag.objects.all()
            if game_id:
                queryset = queryset.filter(game_id=game_id)
            if game_name:
                queryset = queryset.filter(game__name__iexact=game_name)

            featured_qs = queryset.filter(is_featured=True)
            if featured_qs.exists():
                queryset = featured_qs

            tags = queryset.order_by('-usage_count', 'name')[:limit]
            serializer = GameTagSerializer(tags, many=True)
            response["msg"] = "fetched"
            response["data"] = serializer.data
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            response["msg"] = "Something went wrong"
            response["error"] = str(e)
            response["data"] = []
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
