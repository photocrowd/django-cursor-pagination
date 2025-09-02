from base64 import b64decode, b64encode
from collections.abc import Sequence

from django.db.models import F, Q, TextField, Value
from django.utils.translation import gettext_lazy as _


class CursorStrategy:
    """Base interface for cursor pagination strategies."""

    def get_ordering(self, ordering, from_last=False):
        """Transform ordering fields for database queries according to the strategy."""
        raise NotImplementedError

    def build_cursor_filter(
        self, ordering, cursor_values, reverse=False, from_last=False
    ):
        """Build the cursor filter using the strategy's approach."""
        raise NotImplementedError


class DefaultCursorStrategy(CursorStrategy):
    """Default strategy maintaining current NULLS LAST behavior."""

    def get_ordering(self, ordering, from_last=False):
        """
        Transform ordering fields with explicit NULL handling for consistent behavior.

        This clarifies that NULL values come at the end in the sort.
        When "from_last" is specified, NULL values come first since we return
        the results in reversed order.
        """
        nulls_ordering = []
        for key in ordering:
            is_reversed = key.startswith('-')
            column = key.lstrip('-')
            if is_reversed:
                if from_last:
                    nulls_ordering.append(F(column).desc(nulls_first=True))
                else:
                    nulls_ordering.append(F(column).desc(nulls_last=True))
            else:
                if from_last:
                    nulls_ordering.append(F(column).asc(nulls_first=True))
                else:
                    nulls_ordering.append(F(column).asc(nulls_last=True))

        return nulls_ordering

    def build_cursor_filter(
        self, ordering, cursor_values, reverse=False, from_last=False
    ):
        """
        Build the cursor filter using the current OR logic and NULL handling.
        This is the existing implementation from the apply_cursor method.
        """
        if not ordering or not cursor_values:
            return Q()

        if len(ordering) != len(cursor_values):
            raise ValueError("Ordering and cursor values must match length")

        # Convert cursor values for comparison
        position_values = [
            Value(pos, output_field=TextField()) if pos is not None else None
            for pos in cursor_values
        ]

        # Build Q object with OR logic and NULL handling (current implementation)
        filtering = Q()
        q_equality = {}

        for ordering_field, value in zip(ordering, position_values):
            is_reversed = ordering_field.startswith('-')
            o = ordering_field.lstrip('-')
            if value is None:  # cursor value for the key was NULL
                key = "{}__isnull".format(o)
                if (
                    from_last is True
                ):  # if from_last & cursor value is NULL, we need to get non Null for the key
                    q = {key: False}
                    q.update(q_equality)
                    filtering |= Q(**q)

                q_equality.update({key: True})
            else:  # cursor value for the key was non NULL
                if reverse != is_reversed:
                    comparison_key = "{}__lt".format(o)
                else:
                    comparison_key = "{}__gt".format(o)

                q = Q(**{comparison_key: value})
                if not from_last:  # if not from_last, NULL values are still candidates
                    q |= Q(**{"{}__isnull".format(o): True})
                filtering |= (q) & Q(**q_equality)

                equality_key = "{}__exact".format(o)
                q_equality.update({equality_key: value})

        return filtering


class PreserveOrderingStrategy(DefaultCursorStrategy):
    """
    Cursor strategy that preserves the ordering of the fields.
    """

    def get_ordering(self, ordering, from_last=False):
        """
        Return simple ordering fields.
        """
        return ordering


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
        return '<Page: [%s%s]>' % (
            ', '.join(repr(i) for i in self.items[:21]),
            ' (remaining truncated)' if len(self.items) > 21 else '',
        )


class CursorPaginator(object):
    delimiter = '|'
    none_string = '::None'
    invalid_cursor_message = _('Invalid cursor')

    def __init__(self, queryset, ordering, strategy=None):
        self.ordering = ordering
        self.strategy = strategy or DefaultCursorStrategy()
        self.queryset = queryset.order_by(*self._get_ordering(ordering))

    def _get_ordering(self, ordering):
        """Get database ordering using the current strategy."""
        return self.strategy.get_ordering(ordering)

    def _nulls_ordering(self, ordering, from_last=False):
        """Deprecated: Use strategy.get_ordering instead."""
        return self.strategy.get_ordering(ordering, from_last)

    def _apply_paginator_arguments(
        self, qs, first=None, last=None, after=None, before=None
    ):
        """
        Apply first/after, last/before filtering to the queryset
        """
        from_last = last is not None
        if from_last and first is not None:
            raise ValueError('Cannot process first and last')

        if after is not None:
            qs = self.apply_cursor(after, qs, from_last=from_last)
        if before is not None:
            qs = self.apply_cursor(before, qs, from_last=from_last, reverse=True)
        if first is not None:
            qs = qs[: first + 1]
        if last is not None:
            qs = qs.order_by(
                *self._nulls_ordering(reverse_ordering(self.ordering), from_last=True)
            )[: last + 1]

        return qs

    def _get_cursor_page(self, items, has_additional, first, last, after, before):
        """
        Create and return the cursor page for the given items
        """
        additional_kwargs = {}
        if first is not None:
            additional_kwargs['has_next'] = has_additional
            additional_kwargs['has_previous'] = bool(after)
        elif last is not None:
            additional_kwargs['has_previous'] = has_additional
            additional_kwargs['has_next'] = bool(before)
        return CursorPage(items, self, **additional_kwargs)

    def page(self, first=None, last=None, after=None, before=None):
        qs = self.queryset
        qs = self._apply_paginator_arguments(qs, first, last, after, before)

        qs = list(qs)
        page_size = first if first is not None else last
        items = qs[:page_size]
        if last is not None:
            items.reverse()
        has_additional = len(qs) > len(items)

        return self._get_cursor_page(items, has_additional, first, last, after, before)

    async def apage(self, first=None, last=None, after=None, before=None):
        qs = self.queryset
        qs = self._apply_paginator_arguments(qs, first, last, after, before)

        page_size = first if first is not None else last
        items = []
        async for item in qs[:page_size].aiterator():
            items.append(item)
        if last is not None:
            items.reverse()
        has_additional = (await qs.acount()) > len(items)

        return self._get_cursor_page(items, has_additional, first, last, after, before)

    def apply_cursor(self, cursor, queryset, from_last, reverse=False):
        """Apply cursor using the current strategy."""
        position = self.decode_cursor(cursor)
        return queryset.filter(
            self.strategy.build_cursor_filter(
                self.ordering, position, reverse, from_last
            )
        )

    def decode_cursor(self, cursor):
        try:
            orderings = b64decode(cursor.encode('ascii')).decode('utf8')
            return [
                ordering if ordering != self.none_string else None
                for ordering in orderings.split(self.delimiter)
            ]
        except (TypeError, ValueError):
            raise InvalidCursor(self.invalid_cursor_message)

    def encode_cursor(self, position):
        encoded = b64encode(self.delimiter.join(position).encode('utf8')).decode(
            'ascii'
        )
        return encoded

    def position_from_instance(self, instance):
        position = []
        for order in self.ordering:
            parts = order.lstrip('-').split('__')
            attr = instance
            while parts:
                attr = getattr(attr, parts[0])
                parts.pop(0)
            if attr is None:
                position.append(self.none_string)
            else:
                position.append(str(attr))
        return position

    def cursor(self, instance):
        return self.encode_cursor(self.position_from_instance(instance))

    @classmethod
    def for_preserve_ordering(cls, queryset, ordering):
        """Create cursor paginator using PreserveOrderingStrategy."""
        return cls(queryset, ordering, strategy=PreserveOrderingStrategy())

    @classmethod
    def with_strategy(cls, queryset, ordering, strategy):
        """Create a cursor paginator with a custom strategy."""
        return cls(queryset, ordering, strategy=strategy)
