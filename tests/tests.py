# -*- coding: utf-8 -*-

import datetime

from django.test import TestCase
from django.utils import timezone

from cursor_pagination import CursorPaginator

from .models import Author, Post


class TestNoArgs(TestCase):
    def test_empty(self):
        paginator = CursorPaginator(Post.objects.all(), ("id",))
        page = paginator.page()
        self.assertEqual(len(page), 0)
        self.assertFalse(page.has_next)
        self.assertFalse(page.has_previous)

    async def test_async_empty(self):
        paginator = CursorPaginator(Post.objects.all(), ("id",))
        page = await paginator.apage()
        self.assertEqual(len(page), 0)
        self.assertFalse(page.has_next)
        self.assertFalse(page.has_previous)

    def test_with_items(self):
        for i in range(20):
            Post.objects.create(name="Name %s" % i)
        paginator = CursorPaginator(Post.objects.all(), ("id",))
        page = paginator.page()
        self.assertEqual(len(page), 20)
        self.assertFalse(page.has_next)
        self.assertFalse(page.has_previous)

    async def test_async_with_items(self):
        for i in range(20):
            await Post.objects.acreate(name="Name %s" % i)
        paginator = CursorPaginator(Post.objects.all(), ("id",))
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
                name="Name %s" % i, created=now - datetime.timedelta(hours=i)
            )
            cls.items.append(post)
        cls.paginator = CursorPaginator(Post.objects.all(), ("-created",))

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
                name="Name %s" % i, created=now - datetime.timedelta(hours=i)
            )
            cls.items.append(post)
        cls.paginator = CursorPaginator(Post.objects.all(), ("-created",))

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
            (now, "B 横浜市"),
            (now, "C"),
            (now, "D 横浜市"),
            (now + datetime.timedelta(hours=1), "A"),
        ]
        for time, name in data:
            post = Post.objects.create(name=name, created=time)
            cls.items.append(post)

    def test_order(self):
        paginator = CursorPaginator(Post.objects.all(), ("created", "name"))
        previous_page = paginator.page(first=2)
        self.assertSequenceEqual(previous_page, [self.items[0], self.items[1]])
        cursor = paginator.cursor(previous_page[-1])
        page = paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[2], self.items[3]])

    def test_reverse_order(self):
        paginator = CursorPaginator(Post.objects.all(), ("-created", "-name"))
        previous_page = paginator.page(first=2)
        self.assertSequenceEqual(previous_page, [self.items[3], self.items[2]])
        cursor = paginator.cursor(previous_page[-1])
        page = paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[1], self.items[0]])

    def test_mixed_order(self):
        paginator = CursorPaginator(Post.objects.all(), ("created", "-name"))
        previous_page = paginator.page(first=2)
        self.assertSequenceEqual(previous_page, [self.items[2], self.items[1]])
        cursor = paginator.cursor(previous_page[-1])
        page = paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[0], self.items[3]])


class TestRelationships(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.items = []
        author_1 = Author.objects.create(name="Ana")
        author_2 = Author.objects.create(name="Bob")
        for i in range(20):
            post = Post.objects.create(
                name="Name %02d" % i, author=author_1 if i % 2 else author_2
            )
            cls.items.append(post)
        cls.paginator = CursorPaginator(Post.objects.all(), ("author__name", "name"))

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
            Author.objects.create(name="Alice", age=30),
            Author.objects.create(name="Bob", age=None),
            Author.objects.create(name="Carol", age=None),
            Author.objects.create(name="Dave", age=40),
        ]
        paginator = CursorPaginator(
            Author.objects.all(),
            (
                "-age",
                "id",
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
                name="Name %s" % i,
                age=i + 20,
                created=now - datetime.timedelta(hours=i),
            )
            cls.items.append(author)
        for i in range(5):  # index 2-6
            author = Author.objects.create(
                name="NameNull %s" % (i + 2),
                age=None,
                created=now - datetime.timedelta(hours=i),
            )
            cls.items.append(author)
        cls.paginator = CursorPaginator(
            Author.objects.all(),
            (
                "-age",
                "-created",
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
                name="Name %s" % i,
                age=i + 20,
                created=now - datetime.timedelta(hours=i),
            )
            cls.items.append(author)
        for i in range(5):  # index 2-6
            author = Author.objects.create(
                name="NameNull %s" % (i + 2),
                age=None,
                created=now - datetime.timedelta(hours=i),
            )
            cls.items.append(author)
        cls.paginator = CursorPaginator(
            Author.objects.all(),
            (
                "-age",
                "-created",
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
        author_1 = Author.objects.create(name="Ana", age=25)  # odd number
        author_2 = Author.objects.create(name="Bob")  # even number
        for i in range(20):
            post = Post.objects.create(
                name="Name %02d" % i, author=author_1 if i % 2 else author_2
            )
            cls.items.append(post)
        cls.paginator = CursorPaginator(Post.objects.all(), ("author__age", "name"))

    def test_first_page(self):
        page = self.paginator.page(first=2)
        self.assertSequenceEqual(
            page, [self.items[1], self.items[3]]
        )  # Ana comes first

    def test_after_page(self):
        cursor = self.paginator.cursor(self.items[17])
        page = self.paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[19], self.items[0]])


class TestRelationshipsValues(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.items = []
        author_1 = Author.objects.create(name="Ana")
        author_2 = Author.objects.create(name="Bob")
        for i in range(20):
            post = Post.objects.create(
                name="Name %02d" % i, author=author_1 if i % 2 else author_2
            )
            cls.items.append(post)
        cls.paginator = CursorPaginator(
            Post.objects.all().values("author__name", "name"), ("author__name", "name")
        )

    def test_first_page(self):
        page = self.paginator.page(first=2)
        self.assertSequenceEqual(page, [self.items[1], self.items[3]])

    def test_after_page(self):
        cursor = self.paginator.cursor(self.items[17])
        page = self.paginator.page(first=2, after=cursor)
