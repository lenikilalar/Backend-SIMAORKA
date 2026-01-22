from rest_framework import viewsets, permissions, decorators, response, status
from .models import Event, EventAttendance
from .serializers import EventSerializer, EventAttendanceSerializer
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Events'])
class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = self.request.query_params.get('org_id')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        return queryset.order_by('start_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @decorators.action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def attendance(self, request, pk=None):
        event = self.get_object()
        user = request.user
        new_status = request.data.get('status')
        
        if not new_status:
            return response.Response({'error': 'Status required'}, status=status.HTTP_400_BAD_REQUEST)

        attendance, created = EventAttendance.objects.update_or_create(
            event=event, user=user,
            defaults={'status': new_status}
        )
        
        return response.Response({'status': attendance.status, 'marked_at': attendance.marked_at})
