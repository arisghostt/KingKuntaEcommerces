from django.urls import path

from .views import EventDetailView, EventListCreateView


urlpatterns = [
    path('events/', EventListCreateView.as_view(), name='admin-event-list-create'),
    path('events/<uuid:pk>/', EventDetailView.as_view(), name='admin-event-detail'),
]
