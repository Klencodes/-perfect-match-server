from rest_framework import pagination
class LargeCustomPagination(pagination.PageNumberPagination):
    page_size = 20
    page_query_param = 'page'
    page_size_query_param = 'per_page'
    max_page_size = 1000
    
class CustomPagination(pagination.PageNumberPagination):
    page_size = 10
    page_query_param = 'page'
    page_size_query_param = 'per_page'
    max_page_size = 1000

class ShortCustomPagination(pagination.PageNumberPagination):
    page_size = 4
    page_query_param = 'page'
    page_size_query_param = 'per_page'
    max_page_size = 1000