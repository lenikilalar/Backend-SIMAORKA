from rest_framework import viewsets, permissions, decorators, response
from .models import DiscussionThread, DiscussionPost, ChatThread, ChatMessage
from .serializers import DiscussionThreadSerializer, DiscussionPostSerializer, ChatThreadSerializer, ChatMessageSerializer
from apps.organizations.models import Organization

class DiscussionViewSet(viewsets.ModelViewSet):
    queryset = DiscussionThread.objects.all()
    serializer_class = DiscussionThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = self.request.query_params.get('org_id')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @decorators.action(detail=True, methods=['get', 'post'])
    def posts(self, request, pk=None):
        thread = self.get_object()
        
        if request.method == 'GET':
            posts = thread.posts.all().order_by('created_at')
            return response.Response(DiscussionPostSerializer(posts, many=True).data)
        
        elif request.method == 'POST':
            serializer = DiscussionPostSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(thread=thread, created_by=request.user)
            return response.Response(serializer.data, status=201)

class ChatViewSet(viewsets.ModelViewSet):
    queryset = ChatThread.objects.all()
    serializer_class = ChatThreadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only show threads user is part of
        return super().get_queryset().filter(participants__user=self.request.user)

    @decorators.action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        thread = self.get_object()
        content = request.data.get('content')
        if not content:
            return response.Response({'error': 'Content required'}, status=400)
        
        msg = ChatMessage.objects.create(thread=thread, sender=request.user, content=content)
        return response.Response(ChatMessageSerializer(msg).data)
