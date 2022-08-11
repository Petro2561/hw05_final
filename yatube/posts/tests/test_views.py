import os
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

User = get_user_model()

TEMP_ROOT = settings.BASE_DIR + os.sep + "temp"
os.makedirs(TEMP_ROOT, exist_ok=True)
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=TEMP_ROOT)

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.user_author = User.objects.create_user(username='UserAuthor')
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый',
            slug='test-slug',
            description='Тестовое',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая_2',
            slug='test-slug-2',
            description='Тестовое_2',
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='posts/image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_lists',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            self.post.author.username}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            self.post.id}): 'posts/post_create.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.id, self.post.id)
        self.assertEqual(first_object.image, self.post.image)

    def test_index_page_cache(self):
        """Тестируем кэширование"""
        post_cache = Post.objects.create(
            author=self.user,
            text='Кэш пост'
        )
        response = self.authorized_client.get(reverse('posts:index'))
        content_1 = response.content
        post_cache.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        content_2 = response.content
        self.assertEqual(content_1, content_2)
        cache.clear()

        response = self.authorized_client.get(reverse('posts:index'))
        content_3 = response.content
        self.assertNotEqual(content_1, content_3)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:group_lists', kwargs={'slug': 'test-slug'}))
        )
        self.assertEqual(response.context.get('group').title, self.group.title)
        self.assertEqual(response.context.get('group').slug, self.group.slug)
        self.assertEqual(response.context.get('group').description,
                         self.group.description)
        self.assertEqual(response.context.get('group').id, self.group.id)
        self.assertEqual(response.context.get('post').image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.id, self.post.id)
        self.assertEqual(first_object.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        first_object = response.context.get('post')
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.id, self.post.id)
        self.assertEqual(first_object.image, self.post.image)

    def test_post_create_edit_show_correct_context(self):
        """Тестируем страницы post_edit и post_create"""
        pages = {
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
        }
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for page in pages:
            response = self.authorized_client.get(page)
            for val, expected in form_fields.items():
                with self.subTest(val=val):
                    form_field = response.context.get('form').fields.get(val)
                    self.assertIsInstance(form_field, expected)

    def test_group_post_correct_group(self):
        """При создании поста с группой пост оказывается на главной,
        странице группы и странице профайла"""
        pages = (
            reverse('posts:index'),
            reverse('posts:group_lists', kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}),
        )
        for page in pages:
            response = self.authorized_client.get(page)
            page_obj = response.context['page_obj']
            for post in page_obj:
                with self.subTest():
                    self.assertEqual(post.group, self.group)
                    self.assertNotEqual(post.group, self.group_2)

    def test_only_authorized_user_can_comment(self):
        """Проверяем, что пост может комментировать только
        авторизованный пользователь."""
        reverse_name = reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}
        )
        form_data = {
            'text': 'Текст комментария'
        }
        self.assertEqual(self.post.comments.count(), 0)
        self.authorized_client.post(
            reverse_name,
            data=form_data,
            follow=True
        )
        self.assertEqual(self.post.comments.count(), 1)
        self.client.post(
            reverse_name,
            data=form_data,
            follow=True
        )
        self.assertEqual(self.post.comments.count(), 1)

    def test_authorized_client_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок."""
        Follow.objects.get_or_create(
            user=self.user,
            author=self.user_author
        )
        obj_number = Follow.objects.filter(
            user=self.user,
            author=self.user_author
        )
        self.assertEqual(obj_number.count(), 1)
        Follow.objects.filter(
            user=self.user,
            author=self.user_author
        ).delete()
        self.assertEqual(obj_number.count(), 0)

    def test_new_post_for_follower(self):
        new_post = Post.objects.create(
            text='Новый пост',
            author=self.user_author
        )
        Follow.objects.create(
            user=self.user,
            author=self.user_author
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        new_posts = response.context.get('page_obj')
        self.assertIn(new_post,new_posts)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая',
            slug='test-slug',
            description='Теcтовое',
        )
        cls.posts_amount = 13
        cls.posts = []
        for i in range(cls.posts_amount):
            cls.posts.append(Post(
                text=f'Тестовый {i}',
                author=cls.user,
                group=cls.group,
            ))
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_paginator_is_correct(self):
        """Тестируем корректность работы пагинатора."""
        objects_for_second_page = self.posts_amount - settings.OBJECTS_PER_PAGE
        page_context = {
            reverse('posts:index'): settings.OBJECTS_PER_PAGE,
            (reverse('posts:index') + '?page=2'): objects_for_second_page,
            reverse('posts:group_lists', kwargs={'slug': self.group.slug}):
            settings.OBJECTS_PER_PAGE,
            (reverse('posts:group_lists', kwargs={'slug': self.group.slug})
             + '?page=2'): objects_for_second_page,
            reverse('posts:profile', kwargs={'username': self.user.username}):
            settings.OBJECTS_PER_PAGE,
            (reverse('posts:profile', kwargs={'username': self.user.username})
             + '?page=2'): objects_for_second_page
        }
        for reverse_name, post_number in page_context.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                response_number = len(response.context['page_obj'])
                self.assertEqual(response_number, post_number)
