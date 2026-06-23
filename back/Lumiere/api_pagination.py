from math import ceil

from rest_framework.response import Response


def _positive_int(value, default, maximum=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default

    parsed = max(1, parsed)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


def list_response(request, queryset, serializer_class, *, context=None, max_page_size=50):
    limit = request.query_params.get('limit')
    page = request.query_params.get('page')
    page_size = request.query_params.get('page_size')
    serializer_context = context or {'request': request}

    if limit is not None and page is None and page_size is None:
        size = _positive_int(limit, 5, max_page_size)
        serializer = serializer_class(queryset[:size], many=True, context=serializer_context)
        return Response(serializer.data)

    if page is not None or page_size is not None:
        current_page = _positive_int(page, 1)
        size = _positive_int(page_size, 10, max_page_size)
        count = queryset.count()
        start = (current_page - 1) * size
        end = start + size
        serializer = serializer_class(queryset[start:end], many=True, context=serializer_context)
        total_pages = ceil(count / size) if count else 0
        return Response(
            {
                'count': count,
                'page': current_page,
                'page_size': size,
                'total_pages': total_pages,
                'next': current_page + 1 if current_page < total_pages else None,
                'previous': current_page - 1 if current_page > 1 and total_pages else None,
                'results': serializer.data,
            }
        )

    serializer = serializer_class(queryset, many=True, context=serializer_context)
    return Response(serializer.data)
