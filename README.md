Django cursor pagination [![Build Status](https://travis-ci.org/photocrowd/django-cursor-pagination.svg?branch=master)](https://travis-ci.org/photocrowd/django-cursor-pagination)
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
        'last_cursor': paginator.cursor(page[-1])
    }
    return data
```

Reverse pagination can be achieved by using the `last` and `before` arguments
to `paginator.page`.

Caveats
-------

- The ordering specified **must** uniquely identify the object.
- If there are multiple ordering fields, then they must all have the same
  direction
- No support for multiple ordering fields in SQLite as it does not support
  tuple comparison.
- If a cursor is given and it does not refer to a valid object, the values of
  `has_previous` (for `after`) or `has_next` (for `before`) will always return
  `True`.
