import datetime

from django.test import TestCase
from django.utils import timezone

from cursor_pagination import CursorPaginator

from .models import Post


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
        self.assertFalse(page.has_previous)

    def test_last_page(self):
        previous_page = self.paginator.page(first=18)
        cursor = self.paginator.cursor(previous_page[-1])
        page = self.paginator.page(first=2, after=cursor)
        self.assertSequenceEqual(page, [self.items[18], self.items[19]])
        self.assertFalse(page.has_next)
        self.assertFalse(page.has_previous)

    def test_incomplete_last_page(self):
        previous_page = self.paginator.page(first=18)
        cursor = self.paginator.cursor(previous_page[-1])
        page = self.paginator.page(first=100, after=cursor)
        self.assertSequenceEqual(page, [self.items[18], self.items[19]])
        self.assertFalse(page.has_next)
        self.assertFalse(page.has_previous)


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
        self.assertFalse(page.has_next)

    def test_last_page(self):
        previous_page = self.paginator.page(last=18)
        cursor = self.paginator.cursor(previous_page[0])
        page = self.paginator.page(last=2, before=cursor)
        self.assertSequenceEqual(page, [self.items[0], self.items[1]])
        self.assertFalse(page.has_previous)
        self.assertFalse(page.has_next)

    def test_incomplete_last_page(self):
        previous_page = self.paginator.page(last=18)
        cursor = self.paginator.cursor(previous_page[0])
        page = self.paginator.page(last=100, before=cursor)
        self.assertSequenceEqual(page, [self.items[0], self.items[1]])
        self.assertFalse(page.has_previous)
        self.assertFalse(page.has_next)
