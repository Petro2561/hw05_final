from django.contrib import admin
from .models import Comment, Follow, Group, Post


class CommentInline(admin.TabularInline):
    model = Comment


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'
    inlines = [CommentInline]


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Follow)
admin.site.register(Comment)
