from rest_framework.pagination import CursorPagination


class EventCursorPagination(CursorPagination):
    page_size = 100
    ordering = "changed_at"
    cursor_query_param = "cursor"
