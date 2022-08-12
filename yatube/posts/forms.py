from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ('group', 'text', 'image')
        labels = {'text': 'Текст поста', 'group': 'Группа'}


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        help_texts = {'text': 'Напишите комментарий'}
        labels = {'text': 'Комментарий'}
