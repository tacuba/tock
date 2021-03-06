from functools import wraps
import csv
import io
import datetime

from django.conf import settings
from django.shortcuts import render, resolve_url
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.views.generic import ListView
from django.views.generic.edit import FormView
from django.core import exceptions
from django.utils.decorators import method_decorator, available_attrs
from django.utils.six.moves.urllib.parse import urlparse
from django.core.exceptions import PermissionDenied

from tock.remote_user_auth import email_to_username

from .forms import UserForm
from .models import UserData


def parse_date(date):
    if date == 'NA':
        return None
    else:
        return datetime.datetime.strptime(date, '%m/%d/%Y')
        
# Create your views here.
class UserListView(ListView):
    model = User
    template_name = 'employees/user_list.html'

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        return context


class UserFormView(FormView):
    template_name = 'employees/user_form.html'
    form_class = UserForm

    def get_context_data(self, **kwargs):
        kwargs['username'] = self.kwargs['username']
        return super(UserFormView, self).get_context_data(**kwargs)

    def dispatch(self, *args, **kwargs):
        if (self.request.user.is_superuser) or (self.request.user.username == self.kwargs['username']):
            return super(UserFormView, self).dispatch(*args, **kwargs)
        else:
            raise PermissionDenied
    
    def get_initial(self):
        initial = super(UserFormView, self).get_initial()
        user, created = User.objects.get_or_create(username=self.kwargs['username'])
        initial['email'] = user.email
        initial['first_name'] = user.first_name
        initial['last_name'] = user.last_name

        if hasattr(user, 'user_data'):
            initial['start_date'] = user.user_data.start_date
            initial['end_date'] = user.user_data.end_date

        return initial

    def form_valid(self, form):
        if form.is_valid():
            user, created = User.objects.get_or_create(username=self.kwargs['username'])
            user.email = form.cleaned_data['email']
            user.username = email_to_username(form.cleaned_data['email'])
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            user_data, created = UserData.objects.get_or_create(user=user)
            user_data.start_date = form.cleaned_data['start_date']
            user_data.end_date = form.cleaned_data['end_date']
            user_data.save()
        return super(UserFormView, self).form_valid(form)

    def get_success_url(self):
        return reverse("employees:UserListView", current_app=self.request.resolver_match.namespace)