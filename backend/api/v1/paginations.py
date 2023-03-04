from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    """
    Default PageNumberPagination, but "page_size" param is renamed to "limit".
    """
    page_size_query_param = 'limit'
