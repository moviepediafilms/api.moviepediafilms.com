from rest_framework import response


def paginated_response(view, queryset):
    page = view.paginate_queryset(queryset)
    if page is not None:
        serializer = view.get_serializer(instance=page, many=True)
        return view.get_paginated_response(serializer.data)
    serializer = view.get_serializer(instance=queryset, many=True)
    return response.Response(serializer.data)
