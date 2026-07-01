"""Projects API views."""

from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.projects.mixins import OrganizationQuerysetMixin
from apps.projects.models import Project
from apps.projects.permissions import IsOrganizationMember
from apps.projects.serializers import ProjectCreateSerializer, ProjectSerializer


class ProjectViewSet(
    OrganizationQuerysetMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD for projects scoped to the active organization."""

    permission_classes = (IsAuthenticated, IsOrganizationMember)
    lookup_field = "pk"

    def get_queryset(self):
        queryset = Project.objects.all()
        return self.filter_queryset_by_organization(queryset)

    def get_serializer_class(self):
        if self.action == "create":
            return ProjectCreateSerializer
        return ProjectSerializer

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output = ProjectSerializer(serializer.instance)
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer) -> None:
        serializer.save(organization_id=self.request.organization_id)

    def perform_update(self, serializer) -> None:
        serializer.save(organization_id=self.request.organization_id)
