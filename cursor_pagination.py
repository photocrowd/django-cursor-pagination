from base64 import b64decode, b64encode
from collections.abc import Sequence

from django.db.models import Q, TextField, Value
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ugettext_lazy as _


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
            additional_kwargs['has_previous'] = bool(after)
        elif last is not None:
            additional_kwargs['has_previous'] = has_additional
            additional_kwargs['has_next'] = bool(before)
        return CursorPage(items, self, **additional_kwargs)

    def apply_cursor(self, cursor, queryset, reverse=False):
        position = self.decode_cursor(cursor)

        filtering = Q()
        q_acc = []

        # this was previously implemented as tuple comparison done on postgres side
        # Assume comparing 3-tuples a and b,
        # the comparison a < b is equivalent to:
        # (a.0 < b.0) || (a.0 == b.0 && (a.1 < b.1)) || (a.0 == b.0 && a.1 == b.1 && (a.2 < b.2))
        # The expression above does not depend on short-circuit evalution support,
        # which is usually unavailable on backend RDB

        for position, ordering in zip(position, self.ordering):

            is_reversed = ordering.startswith('-')
            o = ordering.lstrip('-')

            if reverse != is_reversed:
                key_cmp = "{}__lt".format(o)
            else:
                key_cmp = "{}__gt".format(o)

            key_eq = "{}__exact".format(o)

            value = Value(position, output_field=TextField())

            q = {key_cmp: value}
            for q_eq in q_acc:
                q.update(q_eq)

            filtering |= Q(**q)

            q_acc.append({key_eq: value})

        return queryset.filter(filtering)

    def decode_cursor(self, cursor):
        try:
            orderings = b64decode(cursor.encode('ascii')).decode('utf8')
            return orderings.split(self.delimiter)
        except (TypeError, ValueError):
            raise InvalidCursor(self.invalid_cursor_message)

    def encode_cursor(self, position):
        encoded = b64encode(self.delimiter.join(position).encode('utf8')).decode('ascii')
        return encoded

    def position_from_instance(self, instance):
        position = []
        for order in self.ordering:
            parts = order.lstrip('-').split('__')
            attr = instance
            while parts:
                attr = getattr(attr, parts[0])
                parts.pop(0)
            position.append(str(attr))
        return position

    def cursor(self, instance):
        return self.encode_cursor(self.position_from_instance(instance))
