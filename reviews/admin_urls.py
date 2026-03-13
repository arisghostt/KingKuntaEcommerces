from django.urls import path

from .views import ReviewViewSet

admin_review_approve = ReviewViewSet.as_view({'patch': 'approve'})

urlpatterns = [
    path('reviews/<uuid:pk>/approve/', admin_review_approve, name='admin-review-approve'),
]

