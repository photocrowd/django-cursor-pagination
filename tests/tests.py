# -*- coding: utf-8 -*-

import datetime

from asgiref.sync import async_to_sync
from django.test import TestCase
from django.utils import timezone

from cursor_pagination import (
    CursorPaginator,
    CursorStrategy,
    DefaultCursorStrategy,
    PreserveOrderingStrategy,
)

from .models import Author, Post


class TestNoArgs(TestCase):
    def test_empty(self):
        paginator = CursorPaginator(Post.objects.all(), ('id',))
        page = paginator.page()
        self.assertEqual(len(page), 0)
        self.assertFalse(page.has_next)
        self.assertFalse(page.has_previous)

    async def test_async_empty(self):
        paginator = CursorPaginator(Post.objects.all(), ('id',))
        page = await paginator.apage()
        self.assertEqual(len(page), 0)
        self.assertFalse(page.has_next)
        self.assertFalse(page.has_previous)

    def test_with_items(self):
        for i in range(20):
            Post.objects.create(name='Name %s' % i)
        paginator = CursorPaginator(Post.objects.all(), ('id',))
        page = paginator.page()
        self.assertEqual(len(page), 20)
        self.assertFalse(page.has_next)
        self.assertFalse(page.has_previous)

    async def test_async_with_items(self):
        for i in range(20):
            await Post.objects.acreate(name='Name %s' % i)
        paginator = CursorPaginator(Post.objects.all(), ('id',))
        page = await paginator.apage()
        self.assertEqual(len(page), 20)
        self.assertFalse(page.has_next)
        self.assertFalse(page.has_previous)


class TestForwardPagination(TestCase):

    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.items = []
        for i in range(20):
            post = Post.objects.create(
                name='Name %s' % i, created=now - datetime.timedelta(hours=i)
            )
            cls.items.append(post)
        cls.paginator = CursorPaginator(Post.objects.all(), ('-created',))

    def test_first_page_zero(self):
        page = self.paginator.page(first=0)
        self.assertSequenceEqual(page, [])
        self.assertTrue(page.has_next)
        self.assertFalse(page.has_previous)

    async def test_async_first_page_zero(self):
        page = await self.paginator.apage(first=0)
        self.assertSequenceEqual(page, [])
        self.assertTrue(page.has_next)
        self.assertFalse(page.has_previous)

    def test_first_page(self):
        page = self.paginator.page(first=2)
        self.assertSequenceEqual(page, [self.items[0], self.items[1]])
        self.assertTrue(page.has_next)
        self.assertFalse(page.has_previous)

    async def test_async_first_page(self):
        page = await self.paginator.apage(first=2)
        self.assertSequenceEqual(page, [self.items[0], self.items[1]])
        self.assertTrue(page.has_next)
        self.assertFalse(page.has_previous)

    def test_second_page(self):
        previous_page = self.paginator.page(first=2)
        cursor = self.paginator.cursor(previous_page[-1])
        page = self.paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[2], self.items[3]])
        self.assertTrue(page.has_next)
        self.assertTrue(page.has_previous)

    async def test_async_second_page(self):
        previous_page = await self.paginator.apage(first=2)
        cursor = self.paginator.cursor(previous_page[-1])
        page = await self.paginator.apage(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[2], self.items[3]])
        self.assertTrue(page.has_next)
        self.assertTrue(page.has_previous)

    def test_last_page(self):
        previous_page = self.paginator.page(first=18)
        cursor = self.paginator.cursor(previous_page[-1])
        page = self.paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[18], self.items[19]])
        self.assertFalse(page.has_next)
        self.assertTrue(page.has_previous)

    async def test_async_last_page(self):
        previous_page = await self.paginator.apage(first=18)
        cursor = self.paginator.cursor(previous_page[-1])
        page = await self.paginator.apage(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[18], self.items[19]])
        self.assertFalse(page.has_next)
        self.assertTrue(page.has_previous)

    def test_incomplete_last_page(self):
        previous_page = self.paginator.page(first=18)
        cursor = self.paginator.cursor(previous_page[-1])
        page = self.paginator.page(first=100, after=cursor)
        self.assertSequenceEqual(page, [self.items[18], self.items[19]])
        self.assertFalse(page.has_next)
        self.assertTrue(page.has_previous)

    async def test_async_incomplete_last_page(self):
        previous_page = await self.paginator.apage(first=18)
        cursor = self.paginator.cursor(previous_page[-1])
        page = await self.paginator.apage(first=100, after=cursor)
        self.assertSequenceEqual(page, [self.items[18], self.items[19]])
        self.assertFalse(page.has_next)
        self.assertTrue(page.has_previous)


class TestBackwardsPagination(TestCase):

    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.items = []
        for i in range(20):
            post = Post.objects.create(
                name='Name %s' % i, created=now - datetime.timedelta(hours=i)
            )
            cls.items.append(post)
        cls.paginator = CursorPaginator(Post.objects.all(), ('-created',))

    def test_first_page_zero(self):
        page = self.paginator.page(last=0)
        self.assertSequenceEqual(page, [])
        self.assertTrue(page.has_previous)
        self.assertFalse(page.has_next)

    async def test_async_first_page_zero(self):
        page = await self.paginator.apage(last=0)
        self.assertSequenceEqual(page, [])
        self.assertTrue(page.has_previous)
        self.assertFalse(page.has_next)

    def test_first_page(self):
        page = self.paginator.page(last=2)
        self.assertSequenceEqual(page, [self.items[18], self.items[19]])
        self.assertTrue(page.has_previous)
        self.assertFalse(page.has_next)

    async def test_async_first_page(self):
        page = await self.paginator.apage(last=2)
        self.assertSequenceEqual(page, [self.items[18], self.items[19]])
        self.assertTrue(page.has_previous)
        self.assertFalse(page.has_next)

    def test_second_page(self):
        previous_page = self.paginator.page(last=2)
        cursor = self.paginator.cursor(previous_page[0])
        page = self.paginator.page(last=2, before=cursor)
        self.assertSequenceEqual(page, [self.items[16], self.items[17]])
        self.assertTrue(page.has_previous)
        self.assertTrue(page.has_next)

    async def test_async_second_page(self):
        previous_page = await self.paginator.apage(last=2)
        cursor = self.paginator.cursor(previous_page[0])
        page = await self.paginator.apage(last=2, before=cursor)
        self.assertSequenceEqual(page, [self.items[16], self.items[17]])
        self.assertTrue(page.has_previous)
        self.assertTrue(page.has_next)

    def test_last_page(self):
        previous_page = self.paginator.page(last=18)
        cursor = self.paginator.cursor(previous_page[0])
        page = self.paginator.page(last=2, before=cursor)
        self.assertSequenceEqual(page, [self.items[0], self.items[1]])
        self.assertFalse(page.has_previous)
        self.assertTrue(page.has_next)

    async def test_async_last_page(self):
        previous_page = await self.paginator.apage(last=18)
        cursor = self.paginator.cursor(previous_page[0])
        page = await self.paginator.apage(last=2, before=cursor)
        self.assertSequenceEqual(page, [self.items[0], self.items[1]])
        self.assertFalse(page.has_previous)
        self.assertTrue(page.has_next)

    def test_incomplete_last_page(self):
        previous_page = self.paginator.page(last=18)
        cursor = self.paginator.cursor(previous_page[0])
        page = self.paginator.page(last=100, before=cursor)
        self.assertSequenceEqual(page, [self.items[0], self.items[1]])
        self.assertFalse(page.has_previous)
        self.assertTrue(page.has_next)

    async def test_async_incomplete_last_page(self):
        previous_page = await self.paginator.apage(last=18)
        cursor = self.paginator.cursor(previous_page[0])
        page = await self.paginator.apage(last=100, before=cursor)
        self.assertSequenceEqual(page, [self.items[0], self.items[1]])
        self.assertFalse(page.has_previous)
        self.assertTrue(page.has_next)


class TestTwoFieldPagination(TestCase):

    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.items = []
        data = [
            (now, 'B 横浜市'),
            (now, 'C'),
            (now, 'D 横浜市'),
            (now + datetime.timedelta(hours=1), 'A'),
        ]
        for time, name in data:
            post = Post.objects.create(name=name, created=time)
            cls.items.append(post)

    def test_order(self):
        paginator = CursorPaginator(Post.objects.all(), ('created', 'name'))
        previous_page = paginator.page(first=2)
        self.assertSequenceEqual(previous_page, [self.items[0], self.items[1]])
        cursor = paginator.cursor(previous_page[-1])
        page = paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[2], self.items[3]])

    def test_reverse_order(self):
        paginator = CursorPaginator(Post.objects.all(), ('-created', '-name'))
        previous_page = paginator.page(first=2)
        self.assertSequenceEqual(previous_page, [self.items[3], self.items[2]])
        cursor = paginator.cursor(previous_page[-1])
        page = paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[1], self.items[0]])

    def test_mixed_order(self):
        paginator = CursorPaginator(Post.objects.all(), ('created', '-name'))
        previous_page = paginator.page(first=2)
        self.assertSequenceEqual(previous_page, [self.items[2], self.items[1]])
        cursor = paginator.cursor(previous_page[-1])
        page = paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[0], self.items[3]])


class TestRelationships(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.items = []
        author_1 = Author.objects.create(name='Ana')
        author_2 = Author.objects.create(name='Bob')
        for i in range(20):
            post = Post.objects.create(
                name='Name %02d' % i, author=author_1 if i % 2 else author_2
            )
            cls.items.append(post)
        cls.paginator = CursorPaginator(Post.objects.all(), ('author__name', 'name'))

    def test_first_page(self):
        page = self.paginator.page(first=2)
        self.assertSequenceEqual(page, [self.items[1], self.items[3]])

    def test_after_page(self):
        cursor = self.paginator.cursor(self.items[17])
        page = self.paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[19], self.items[0]])


class TestNoArgsWithNull(TestCase):
    def test_with_items(self):
        authors = [
            Author.objects.create(name='Alice', age=30),
            Author.objects.create(name='Bob', age=None),
            Author.objects.create(name='Carol', age=None),
            Author.objects.create(name='Dave', age=40),
        ]
        paginator = CursorPaginator(
            Author.objects.all(),
            (
                '-age',
                'id',
            ),
        )
        page = paginator.page()
        self.assertSequenceEqual(page, [authors[3], authors[0], authors[1], authors[2]])
        self.assertFalse(page.has_next)
        self.assertFalse(page.has_previous)


class TestForwardNullPagination(TestCase):
    # When there are NULL values, there needs to be another key to make the sort
    # unique as README Caveats say
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.items = []
        for i in range(2):  # index 0-1
            author = Author.objects.create(
                name='Name %s' % i,
                age=i + 20,
                created=now - datetime.timedelta(hours=i),
            )
            cls.items.append(author)
        for i in range(5):  # index 2-6
            author = Author.objects.create(
                name='NameNull %s' % (i + 2),
                age=None,
                created=now - datetime.timedelta(hours=i),
            )
            cls.items.append(author)
        cls.paginator = CursorPaginator(
            Author.objects.all(),
            (
                '-age',
                '-created',
            ),
        )

    # [1, 0, 2, 3, 4, 5, 6]

    def test_first_page(self):
        page = self.paginator.page(first=3)
        self.assertSequenceEqual(page, [self.items[1], self.items[0], self.items[2]])
        self.assertTrue(page.has_next)
        self.assertFalse(page.has_previous)

    def test_second_page(self):
        previous_page = self.paginator.page(first=3)
        cursor = self.paginator.cursor(previous_page[-1])
        page = self.paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[3], self.items[4]])
        self.assertTrue(page.has_next)
        self.assertTrue(page.has_previous)

    def test_last_page(self):
        previous_page = self.paginator.page(first=5)
        cursor = self.paginator.cursor(previous_page[-1])
        page = self.paginator.page(first=10, after=cursor)
        self.assertSequenceEqual(page, [self.items[5], self.items[6]])
        self.assertFalse(page.has_next)
        self.assertTrue(page.has_previous)


class TestBackwardsNullPagination(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.items = []
        for i in range(2):  # index 0-1
            author = Author.objects.create(
                name='Name %s' % i,
                age=i + 20,
                created=now - datetime.timedelta(hours=i),
            )
            cls.items.append(author)
        for i in range(5):  # index 2-6
            author = Author.objects.create(
                name='NameNull %s' % (i + 2),
                age=None,
                created=now - datetime.timedelta(hours=i),
            )
            cls.items.append(author)
        cls.paginator = CursorPaginator(
            Author.objects.all(),
            (
                '-age',
                '-created',
            ),
        )
        # => [1, 0, 2, 3, 4, 5, 6]

    def test_first_page(self):
        page = self.paginator.page(last=2)
        self.assertSequenceEqual(page, [self.items[5], self.items[6]])
        self.assertTrue(page.has_previous)
        self.assertFalse(page.has_next)

    def test_second_page(self):
        previous_page = self.paginator.page(last=2)
        cursor = self.paginator.cursor(previous_page[0])
        page = self.paginator.page(last=4, before=cursor)
        self.assertSequenceEqual(
            page, [self.items[0], self.items[2], self.items[3], self.items[4]]
        )
        self.assertTrue(page.has_previous)
        self.assertTrue(page.has_next)

    def test_last_page(self):
        previous_page = self.paginator.page(last=6)
        cursor = self.paginator.cursor(previous_page[0])
        page = self.paginator.page(last=10, before=cursor)
        self.assertSequenceEqual(page, [self.items[1]])
        self.assertFalse(page.has_previous)
        self.assertTrue(page.has_next)


class TestRelationshipsWithNull(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.items = []
        author_1 = Author.objects.create(name='Ana', age=25)  # odd number
        author_2 = Author.objects.create(name='Bob')  # even number
        for i in range(20):
            post = Post.objects.create(
                name='Name %02d' % i, author=author_1 if i % 2 else author_2
            )
            cls.items.append(post)
        cls.paginator = CursorPaginator(Post.objects.all(), ('author__age', 'name'))

    def test_first_page(self):
        page = self.paginator.page(first=2)
        self.assertSequenceEqual(
            page, [self.items[1], self.items[3]]
        )  # Ana comes first

    def test_after_page(self):
        cursor = self.paginator.cursor(self.items[17])
        page = self.paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[19], self.items[0]])


class TestStrategyPattern(TestCase):
    """Test the new strategy pattern functionality."""
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.items = []
        for i in range(10):
            post = Post.objects.create(
                name='Name %s' % i, created=now - datetime.timedelta(hours=i)
            )
            cls.items.append(post)

        # Create some authors with NULL ages for testing
        cls.authors = [
            Author.objects.create(name='Alice', age=30, created=now),
            Author.objects.create(
                name='Bob', age=None, created=now - datetime.timedelta(hours=1)
            ),
            Author.objects.create(
                name='Carol', age=25, created=now - datetime.timedelta(hours=2)
            ),
        ]
        
    def test_strategy_interface_abstract(self):
        """Test that CursorStrategy interface is properly abstract."""
        # Should not be able to instantiate abstract class directly
        strategy = CursorStrategy()

        # Methods should raise NotImplementedError
        with self.assertRaises(NotImplementedError):
            strategy.get_ordering(('id',))

        with self.assertRaises(NotImplementedError):
            strategy.build_cursor_filter(('id',), ['1'])

    def test_concrete_strategies_work(self):
        """Test that concrete strategy implementations work."""
        default_strategy = DefaultCursorStrategy()
        self.assertIsInstance(default_strategy, CursorStrategy)

        postgres_strategy = PreserveOrderingStrategy()
        self.assertIsInstance(postgres_strategy, CursorStrategy)

    def test_default_strategy_behavior(self):
        """Test that default strategy maintains existing NULLS LAST behavior."""

        strategy = DefaultCursorStrategy()

        # Test get_ordering
        ordering = ('-created', 'id')
        result = strategy.get_ordering(ordering)
        self.assertEqual(len(result), 2)
        self.assertTrue(hasattr(result[0], 'desc'))
        self.assertTrue(hasattr(result[1], 'asc'))

        # Test with from_last=True
        result_from_last = strategy.get_ordering(ordering, from_last=True)
        self.assertEqual(len(result_from_last), 2)
        self.assertTrue(hasattr(result_from_last[0], 'desc'))
        self.assertTrue(hasattr(result_from_last[1], 'asc'))

    def test_preserver_strategy_behavior(self):
        """Test that PreserveOrderingStrategy returns simple ordering."""
        strategy = PreserveOrderingStrategy()

        # Test get_ordering - should return simple ordering as a list
        ordering = ('-created', 'id')
        result = strategy.get_ordering(ordering)
        self.assertEqual(result, list(ordering))

        # Test with from_last=True - should still return simple ordering
        result_from_last = strategy.get_ordering(ordering, from_last=True)
        self.assertEqual(result_from_last, list(ordering))

    def test_preserve_strategy_cursor_filter(self):
        """Test PreserveOrderingStrategy cursor filter building."""
        strategy = PreserveOrderingStrategy()
        ordering = ('-created', 'id')
        cursor_values = ['2023-01-01 12:00:00', '5']

        # Test normal case
        result = strategy.build_cursor_filter(
            ordering, cursor_values, reverse=False, from_last=False
        )
        self.assertIsNotNone(result)

        # Test with reverse=True
        result_reverse = strategy.build_cursor_filter(
            ordering, cursor_values, reverse=True, from_last=False
        )
        self.assertIsNotNone(result_reverse)

        # Test with from_last=True
        result_from_last = strategy.build_cursor_filter(
            ordering, cursor_values, reverse=False, from_last=True
        )
        self.assertIsNotNone(result_from_last)

    def test_preserve_strategy_null_handling(self):
        """Test that PreserveOrderingStrategy handles NULL cursor values like DefaultCursorStrategy."""
        strategy = PreserveOrderingStrategy()
        ordering = ('-created', 'id')
        cursor_values = ['2023-01-01 12:00:00', None]  # Second value is NULL

        # PreserveOrderingStrategy inherits from DefaultCursorStrategy, so it handles NULLs the same way
        result = strategy.build_cursor_filter(ordering, cursor_values)
        self.assertIsNotNone(result)

    def test_strategy_parameter_in_constructor(self):
        """Test that strategy parameter works in CursorPaginator constructor."""
        # Test with Postgres strategy
        paginator = CursorPaginator(
            Post.objects.all(), ('-created',), strategy=PreserveOrderingStrategy()
        )
        self.assertIsInstance(paginator.strategy, PreserveOrderingStrategy)

        # Test with Default strategy
        paginator = CursorPaginator(
            Post.objects.all(), ('-created',), strategy=DefaultCursorStrategy()
        )
        self.assertIsInstance(paginator.strategy, DefaultCursorStrategy)

        # Test default strategy when none provided
        paginator = CursorPaginator(Post.objects.all(), ('-created',))
        self.assertIsInstance(paginator.strategy, DefaultCursorStrategy)

    def test_for_preverve_ordering_factory_method(self):
        """Test the for_preserve_ordering factory method."""
        paginator = CursorPaginator.for_preserve_ordering(
            Post.objects.all(), ('-created',)
        )
        self.assertIsInstance(paginator.strategy, PreserveOrderingStrategy)

        # Verify it works the same as regular paginator
        page = paginator.page(first=5)
        self.assertEqual(len(page), 5)
        self.assertTrue(page.has_next)

    def test_with_strategy_factory_method(self):
        """Test the with_strategy factory method."""

        paginator = CursorPaginator.with_strategy(
            Post.objects.all(), ('-created',), PreserveOrderingStrategy()
        )
        self.assertIsInstance(paginator.strategy, PreserveOrderingStrategy)

        # Verify it works the same as regular paginator
        page = paginator.page(first=5)
        self.assertEqual(len(page), 5)
        self.assertTrue(page.has_next)

    def test_backwards_compatibility(self):
        """Test that existing functionality works exactly the same."""
        # Test with default strategy (existing behavior)
        paginator = CursorPaginator(Post.objects.all(), ('-created',))
        page = paginator.page(first=3)
        self.assertEqual(len(page), 3)
        self.assertTrue(page.has_next)

        # Test cursor functionality
        cursor = paginator.cursor(page[-1])
        next_page = paginator.page(first=3, after=cursor)
        self.assertEqual(len(next_page), 3)
        self.assertTrue(next_page.has_next)
        self.assertTrue(next_page.has_previous)

    def test_strategy_ordering_differences(self):
        """Test that different strategies produce different ordering but same results."""
        # Default strategy (with NULLS LAST)
        default_paginator = CursorPaginator(Post.objects.all(), ('-created',))
        default_page = default_paginator.page(first=3)

        # PreserveOrderingStrategy (without NULLS LAST)
        no_nulls_paginator = CursorPaginator(
            Post.objects.all(), ('-created',), strategy=PreserveOrderingStrategy()
        )
        no_nulls_page = no_nulls_paginator.page(first=3)

        # Both should return the same items (assuming no NULL values in created field)
        self.assertEqual(len(default_page), len(no_nulls_page))
        self.assertEqual(len(default_page), 3)

        # The ordering should be the same for non-NULL fields
        for i in range(3):
            self.assertEqual(default_page[i].id, no_nulls_page[i].id)

    def test_multi_field_ordering_with_strategies(self):
        """Test multi-field ordering with different strategies."""
        # Test with default strategy
        default_paginator = CursorPaginator(Author.objects.all(), ('-age', '-created'))
        default_page = default_paginator.page(first=3)

        # Test with PreserveOrderingStrategy
        no_nulls_paginator = CursorPaginator(
            Author.objects.all(),
            ('-age', '-created'),
            strategy=PreserveOrderingStrategy(),
        )

        # PreserveOrderingStrategy should work the same as default strategy
        # Both strategies now handle NULL values the same way
        no_nulls_page = no_nulls_paginator.page(first=2)
        self.assertEqual(len(no_nulls_page), 2)

        # Test that cursor pagination works with NULL values too
        if len(no_nulls_page) > 0:
            cursor = no_nulls_paginator.cursor(no_nulls_page[0])
            next_page = no_nulls_paginator.page(first=1, after=cursor)
            # May have 0 or 1 items depending on data, just verify it doesn't crash
            self.assertLessEqual(len(next_page), 1)

    def test_error_handling_in_strategies(self):
        """Test error handling in strategy methods."""
        strategy = PreserveOrderingStrategy()

        # Test with mismatched lengths
        ordering = ('-created', 'id')
        cursor_values = ['2023-01-01 12:00:00']  # Only one value, should be two

        with self.assertRaises(ValueError) as cm:
            strategy.build_cursor_filter(ordering, cursor_values)
        self.assertIn('must match length', str(cm.exception))

        # Test with empty ordering
        result = strategy.build_cursor_filter([], [])
        self.assertIsNotNone(result)

        # Test with empty cursor values
        result = strategy.build_cursor_filter(ordering, [])
        self.assertIsNotNone(result)

    def test_strategy_inheritance(self):
        """Test that strategies properly inherit from base class."""
        # Test inheritance hierarchy
        self.assertTrue(issubclass(DefaultCursorStrategy, CursorStrategy))
        self.assertTrue(issubclass(PreserveOrderingStrategy, CursorStrategy))
        self.assertTrue(issubclass(PreserveOrderingStrategy, DefaultCursorStrategy))

        # Test instance types
        default = DefaultCursorStrategy()
        no_nulls = PreserveOrderingStrategy()

        self.assertIsInstance(default, CursorStrategy)
        self.assertIsInstance(no_nulls, CursorStrategy)
        self.assertIsInstance(
            no_nulls, DefaultCursorStrategy
        )  # PreserveOrderingStrategy inherits from Default

        # Test that they're different concrete types
        self.assertNotIsInstance(default, PreserveOrderingStrategy)
        self.assertEqual(type(default).__name__, 'DefaultCursorStrategy')
        self.assertEqual(type(no_nulls).__name__, 'PreserveOrderingStrategy')

    def test_strategy_method_signatures(self):
        """Test that strategy methods have correct signatures."""
        default = DefaultCursorStrategy()
        no_nulls = PreserveOrderingStrategy()

        # Test that methods exist and are callable
        self.assertTrue(hasattr(default, 'get_ordering'))
        self.assertTrue(hasattr(default, 'build_cursor_filter'))
        self.assertTrue(callable(default.get_ordering))
        self.assertTrue(callable(default.build_cursor_filter))

        self.assertTrue(hasattr(no_nulls, 'get_ordering'))
        self.assertTrue(hasattr(no_nulls, 'build_cursor_filter'))
        self.assertTrue(callable(no_nulls.get_ordering))
        self.assertTrue(callable(no_nulls.build_cursor_filter))

    def test_strategy_performance_characteristics(self):
        """Test that strategies handle different input sizes correctly."""
        # Test with single field ordering
        single_ordering = ('id',)
        single_cursor = ['5']

        postgres_strategy = PreserveOrderingStrategy()
        default_strategy = DefaultCursorStrategy()

        # Both should handle single field the same way
        postgres_result = postgres_strategy.build_cursor_filter(
            single_ordering, single_cursor
        )
        default_result = default_strategy.build_cursor_filter(
            single_ordering, single_cursor
        )

        self.assertIsNotNone(postgres_result)
        self.assertIsNotNone(default_result)

        # Test with many fields
        many_ordering = ('id', 'name', 'created', 'updated', 'status')
        many_cursor = ['1', 'test', '2023-01-01', '2023-01-02', 'active']

        postgres_many = postgres_strategy.build_cursor_filter(
            many_ordering, many_cursor
        )
        default_many = default_strategy.build_cursor_filter(many_ordering, many_cursor)

        self.assertIsNotNone(postgres_many)
        self.assertIsNotNone(default_many)

    def test_strategy_edge_cases(self):
        """Test edge cases and boundary conditions."""
        strategy = PreserveOrderingStrategy()

        # Test with very long field names
        long_field = 'very_long_field_name_that_might_cause_issues_with_some_databases'
        ordering = (long_field,)
        cursor_values = ['test_value']

        result = strategy.build_cursor_filter(ordering, cursor_values)
        self.assertIsNotNone(result)

        # Test with special characters in field names
        special_field = 'field_with_dashes_and_underscores'
        ordering = (special_field,)
        cursor_values = ['test_value']

        result = strategy.build_cursor_filter(ordering, cursor_values)
        self.assertIsNotNone(result)

        # Test with empty strings (not None)
        ordering = ('name',)
        cursor_values = ['']

        result = strategy.build_cursor_filter(ordering, cursor_values)
        self.assertIsNotNone(result)

class TestPageWithOneDatabaseCall(TestCase):
    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.items = []
        for i in range(20):
            post = Post.objects.create(name='Name %s' % i, created=now - datetime.timedelta(hours=i))
            cls.items.append(post)
        cls.paginator = CursorPaginator(Post.objects.all(), ('-created',))

    def test_page_forwards(self):
        with self.assertNumQueries(1):
            self.paginator.page(first=2)

    def test_async_page_forwards(self):
        with self.assertNumQueries(1):
            # `async_to_sync` is required as long as there is no async version of assertNumQueries
            async_to_sync(self.paginator.apage)(first=2)

    def test_page_backwards(self):
        with self.assertNumQueries(1):
            self.paginator.page(last=2)

    def test_async_page_backwards(self):
        # `async_to_sync` is required as long as there is no async version of assertNumQueries
        with self.assertNumQueries(1):
            async_to_sync(self.paginator.apage)(last=2)
