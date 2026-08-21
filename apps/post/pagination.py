from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from rest_framework.response import Response

class PostPagination(PageNumberPagination):
    page_size = 4
    page_size_query_param = 'limit'
    max_page_size = 10
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'current_page_count': len(data),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

class CommentPagination(LimitOffsetPagination):
    default_limit = 5
    max_limit = 20
