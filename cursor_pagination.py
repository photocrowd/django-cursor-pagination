from base64 import b64decode, b64encode
from collections import Sequence

from django.db.models import Field, Func, Value, TextField
from django.utils import six
from django.utils.translation import ugettext_lazy as _


class TupleField(Field):
    pass


class Tuple(Func):
    function = ''
    output_field = TupleField()


class InvalidCursor(Exception):
    pass


def reverse_ordering(ordering_tuple):
    """
    Given an order_by tuple such as `('-created', 'uuid')` reverse the
    ordering and return a new tuple, eg. `('created', '-uuid')`.
    """
    def invert(x):
        return x[1:] if (x.startswith('-')) else '-' + x

    return tuple([invert(item) for item in ordering_tuple])


class CursorPage(Sequence):
    def __init__(self, items, paginator, has_next=False, has_previous=False):
        self.items = items
        self.paginator = paginator
        self.has_next = has_next
        self.has_previous = has_previous

    def __len__(self):
        return len(self.items)

    def __getitem__(self, key):
        return self.items.__getitem__(key)

    def __repr__(self):
        return '<Page: [%s%s]>' % (', '.join(repr(i) for i in self.items[:21]), ' (remaining truncated)' if len(self.items) > 21 else '')


class CursorPaginator(object):
    delimiter = '|'
    invalid_cursor_message = _('Invalid cursor')

    def __init__(self, queryset, ordering):
        self.queryset = queryset.order_by(*ordering)
        self.ordering = ordering

        if not all(o.startswith('-') for o in ordering) and not all(not o.startswith('-') for o in ordering):
            raise InvalidCursor('Direction of orderings must match')

    def page(self, first=None, last=None, after=None, before=None):
        qs = self.queryset
        page_size = first or last
        if page_size is None:
            return CursorPage(qs, self)

        if after is not None:
            qs = self.apply_cursor(after, qs)
        if before is not None:
            qs = self.apply_cursor(before, qs, reverse=True)
        if first is not None:
            qs = qs[:first + 1]
        if last is not None:
            if first is not None:
                raise ValueError('Cannot process first and last')
            qs = qs.order_by(*reverse_ordering(self.ordering))[:last + 1]

        qs = list(qs)
        items = qs[:page_size]
        if last is not None:
            items.reverse()
        has_additional = len(qs) > len(items)
        additional_kwargs = {}
        if first is not None:
            additional_kwargs['has_next'] = has_additional
        elif last is not None:
            additional_kwargs['has_previous'] = has_additional
        return CursorPage(items, self, **additional_kwargs)

    def apply_cursor(self, cursor, queryset, reverse=False):
        position = self.decode_cursor(cursor)

        is_reversed = self.ordering[0].startswith('-')
        queryset = queryset.annotate(cursor=Tuple(*[o.lstrip('-') for o in self.ordering]))
        current_position = [Value(p, output_field=TextField()) for p in position]
        if reverse != is_reversed:
            return queryset.filter(cursor__lt=Tuple(*current_position))
        return queryset.filter(cursor__gt=Tuple(*current_position))

    def decode_cursor(self, cursor):
        try:
            orderings = b64decode(cursor.encode('ascii')).decode('ascii')
            return orderings.split(self.delimiter)
        except (TypeError, ValueError):
            raise InvalidCursor(self.invalid_cursor_message)

    def encode_cursor(self, position):
        encoded = b64encode(self.delimiter.join(position).encode('ascii')).decode('ascii')
        return encoded

    def position_from_instance(self, instance):
        position = []
        for order in self.ordering:
            attr = getattr(instance, order.lstrip('-'))
            position.append(six.text_type(attr))
        return position

    def cursor(self, instance):
        return self.encode_cursor(self.position_from_instance(instance))
