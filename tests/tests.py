import datetime

from django.test import TestCase
from django.utils import timezone

from cursor_pagination import CursorPaginator, InvalidCursor

from .models import Author, Post


class TestNoArgs(TestCase):
    def test_empty(self):
        paginator = CursorPaginator(Post.objects.all(), ('id',))
        page = paginator.page()
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


class TestForwardPagination(TestCase):

    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.items = []
        for i in range(20):
            post = Post.objects.create(name='Name %s' % i, created=now - datetime.timedelta(hours=i))
            cls.items.append(post)
        cls.paginator = CursorPaginator(Post.objects.all(), ('-created',))

    def test_first_page(self):
        page = self.paginator.page(first=2)
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

    def test_last_page(self):
        previous_page = self.paginator.page(first=18)
        cursor = self.paginator.cursor(previous_page[-1])
        page = self.paginator.page(first=2, after=cursor)
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


class TestBackwardsPagination(TestCase):

    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.items = []
        for i in range(20):
            post = Post.objects.create(name='Name %s' % i, created=now - datetime.timedelta(hours=i))
            cls.items.append(post)
        cls.paginator = CursorPaginator(Post.objects.all(), ('-created',))

    def test_first_page(self):
        page = self.paginator.page(last=2)
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

    def test_last_page(self):
        previous_page = self.paginator.page(last=18)
        cursor = self.paginator.cursor(previous_page[0])
        page = self.paginator.page(last=2, before=cursor)
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


class TestTwoFieldPagination(TestCase):

    @classmethod
    def setUpTestData(cls):
        now = timezone.now()
        cls.items = []
        data = [
            (now, 'B'),
            (now, 'C'),
            (now, 'D'),
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
        with self.assertRaises(InvalidCursor):
            CursorPaginator(Post.objects.all(), ('created', '-name'))


class TestRelationships(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.items = []
        author_1 = Author.objects.create(name='Ana')
        author_2 = Author.objects.create(name='Bob')
        for i in range(20):
            post = Post.objects.create(name='Name %02d' % i, author=author_1 if i % 2 else author_2)
            cls.items.append(post)
        cls.paginator = CursorPaginator(Post.objects.all(), ('author__name', 'name'))

    def test_first_page(self):
        page = self.paginator.page(first=2)
        self.assertSequenceEqual(page, [self.items[1], self.items[3]])

    def test_after_page(self):
        cursor = self.paginator.cursor(self.items[17])
        page = self.paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[19], self.items[0]])
