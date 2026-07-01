"""Accounts API views."""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.serializers import RegisterSerializer, UserMeSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Register a new user and optionally create an organization."""

    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output = UserSerializer(user)
        return Response(output.data, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveAPIView):
    """Return the authenticated user and their organization memberships."""

    permission_classes = (IsAuthenticated,)
    serializer_class = UserMeSerializer

    def get_object(self):
        return self.request.user
