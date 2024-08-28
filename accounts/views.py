from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import Response
from rest_framework import status
from rest_framework.views import APIView
from .serializers import PlayerSignupSerializer, TeamSignupSerializer, CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response = response.data
        response["msg"] = "Success"
        return Response(response, status=status.HTTP_200_OK)

class CustomTokenRefreshView(TokenRefreshView):
    pass



class PlayerSignupView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = PlayerSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "Player signup successful"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeamSignupView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = TeamSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "Team signup successful"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
