from django.views.generic import CreateView

from django.urls import reverse_lazy

from .forms import CreationForm, ContactForm

from .models import Contact

from django.shortcuts import render


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


def user_contact(request):
    ...
    # Запрашиваем объект модели Contact
    contact = Contact.objects.get(pk=3)

    # Создаём объект формы и передаём в него объект модели с pk=3
    form = ContactForm(instance=contact)

    return render(request, 'users/contact.html', {'form': form})


def password_change(request):
    return render(request, 'users/password_change.html')
