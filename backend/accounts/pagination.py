from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """Pagination that emits the SRS §19 metadata block."""
    page_size = 20
    page_size_query_param = "per_page"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "results": data,
            "meta": {
                "current_page": self.page.number,
                "per_page": self.get_page_size(self.request),
                "total": self.page.paginator.count,
                "last_page": self.page.paginator.num_pages,
            },
        })
