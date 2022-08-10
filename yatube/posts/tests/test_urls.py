from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='UserAuthor')
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user_author,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        cache.clear()

    def test_urls_exists_at_desired_location_for_any_clients(self):
        """Проверка страниц на доступность любым пользователям"""
        pages = {
            '/': HTTPStatus.OK.value,
            f'/group/{self.group.slug}/': HTTPStatus.OK.value,
            f'/profile/{self.post.author.username}/':
            HTTPStatus.OK.value,
            f'/posts/{self.post.pk}/': HTTPStatus.OK.value,
            f'/posts/{self.post.pk}/edit/': HTTPStatus.FOUND.value,
            '/create/': HTTPStatus.FOUND.value,
            '/unexisting_page/': HTTPStatus.NOT_FOUND.value,
            f'/posts/{self.post.pk}/comment/': HTTPStatus.FOUND.value,
        }
        for url, stat_code in pages.items():
            with self.subTest(url=url):
                self.assertEqual(
                    self.client.get(url).status_code, stat_code)

    def test_urls_for_author(self):
        """"Проверка страницы на доступность автором"""
        response = self.author_client.get(
            f'/posts/{self.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_urls_post_edit_for_authorized_user(self):
        """"Проверка страницы на доступность автором"""
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND.value)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author.username}/':
            'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
