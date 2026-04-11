Django cursor pagination [![Tests](https://github.com/photocrowd/django-cursor-pagination/actions/workflows/tests.yml/badge.svg?event=push)](https://github.com/photocrowd/django-cursor-pagination/actions/workflows/tests.yml)
========================

A cursor based pagination system for Django. Instead of refering to specific
pages by number, we give every item in the queryset a cursor based on its
ordering values. We then ask for subsequent records by asking for records
*after* the cursor of the last item we currently have. Similarly we can ask for
records *before* the cursor of the first item to navigate back through the
list.

This approach has two major advantages over traditional pagination. Firstly, it
ensures that when new data is written into the table, records cannot be moved
onto the next page. Secondly, it is much faster to query against the database
as we are not using very large offset values.

There are some significant drawbacks over "traditional" pagination. The data
must be ordered by some database field(s) which are unique across all records.
A typical use case would be ordering by a creation timestamp and an id. It is
also more difficult to get the range of possible pages for the data.

The inspiration for this project is largely taken from [this
post](http://cra.mr/2011/03/08/building-cursors-for-the-disqus-api) by David
Cramer, and the connection spec for [Relay
GraphQL](https://facebook.github.io/relay/graphql/connections.htm). Much of the
implementation is inspired by [Django rest framework's Cursor
pagination.](https://github.com/tomchristie/django-rest-framework/blob/9b56dda91850a07cfaecbe972e0f586434b965c3/rest_framework/pagination.py#L407-L707).
The main difference between the Disqus approach and the one used here is that
we require the ordering to be totally determinate instead of using offsets.


Installation
------------

```
pip install django-cursor-pagination
```

Development & Testing
--------------------

### Running Tests

1. **Start PostgreSQL with Docker:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Install development dependencies:**
   ```bash
   pip install django 'psycopg[binary]' python-dotenv
   ```

3. **Run tests:**
   ```bash
   python runtests.py                    # Run all tests
   python runtests.py tests.tests.TestForwardPagination  # Run specific test class
   ```

### Database Configuration

The tests use PostgreSQL by default on port 5432. You can override the port if needed:

```bash
# Copy example environment file
cp .env.example .env
# Edit .env to change POSTGRES_PORT if needed
```

Usage
-----

```python
from cursor_pagination import CursorPaginator

from myapp.models import Post


def posts_api(request, after=None):
    qs = Post.objects.all()
    page_size = 10
    paginator = CursorPaginator(qs, ordering=('-created', '-id'))
    page = paginator.page(first=page_size, after=after)
    data = {
        'objects': [serialize_page(p) for p in page],
        'has_next_page': page.has_next,
        'last_cursor': page.after()
    }
    return data


async def posts_api_async(request, after=None):
    qs = Post.objects.all()
    page_size = 10
    paginator = CursorPaginator(qs, ordering=('-created', '-id'))
    page = await paginator.apage(first=page_size, after=after)
    data = {
        'objects': [serialize_page(p) for p in page],
        'has_next_page': page.has_next,
        'last_cursor': paginator.cursor(page[-1])
    }
    return data
```

Reverse pagination can be achieved by using the `last` and `before` arguments
to `paginator.page`.

### Helper Methods

The `CursorPage` object provides `before()` and `after()` helper methods that return cursors for the first and last items in the current page, simplifying pagination navigation:

```python
def posts_api(request):
    qs = Post.objects.all()
    page_size = 10
    paginator = CursorPaginator(qs, ordering=('-created', '-id'))
    
    # Handle pagination parameters
    if 'after' in request.GET:
        page = paginator.page(first=page_size, after=request.GET['after'])
    elif 'before' in request.GET:
        page = paginator.page(last=page_size, before=request.GET['before'])
    else:
        page = paginator.page(first=page_size)
    
    # Use helper methods for navigation cursors
    data = {
        'objects': [serialize_post(p) for p in page],
        'page_info': {
            'has_next_page': page.has_next,
            'has_previous_page': page.has_previous,
            'start_cursor': page.before(),  # Cursor for first item
            'end_cursor': page.after()       # Cursor for last item
        }
    }
    return data
```

This is particularly useful for GraphQL/Relay-style pagination or when building pagination controls in templates:

```django
<!-- In your Django template -->
{% if page_obj.has_previous %}
    <a href="?before={{ page_obj.before }}">Previous</a>
{% endif %}

{% if page_obj.has_next %}
    <a href="?after={{ page_obj.after }}">Next</a>
{% endif %}
```

Caveats
-------

- The ordering specified **must** uniquely identify the object.
- If a cursor is given and it does not refer to a valid object, the values of
  `has_previous` (for `after`) or `has_next` (for `before`) will always return
  `True`.
- `NULL` comes at the end in query results with `ORDER BY` both for `ASC` and `DESC`.
