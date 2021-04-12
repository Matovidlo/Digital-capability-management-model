from allauth.socialaccount.models import SocialToken
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse
from django.template import loader, TemplateDoesNotExist
import requests
import json

from . import forms


def connect_github(request):
    query = SocialToken.objects.filter(account__user=request.user,
                                       account__provider='github')
    form = []
    if query:
        token = query[0]
        print(token)
        headers = {'Authorization': 'token ' + str(token)}
        repos = requests.get('https://api.github.com/user/repos',
                             headers=headers)
        content = list(element['full_name'] for element in json.loads(repos.text))
        form = forms.GithubForm(content)
    return form

@login_required(login_url="/login/")
def gathering(request):
    if request.method == "POST":
        data = dict(request.POST)
        print(data['repositories'])
    form_class = connect_github(request)
    # form_class = forms.GithubForm
    return render(request, 'gathering.html', context={'form': form_class})

@login_required(login_url="/login/")
def visualisations(request):
    return render(request, 'visualisations.html')

@login_required(login_url="/login/")
def settings(request):
    context = {'segment': 'settings'}
    html_template = loader.get_template('settings.html')
    return HttpResponse(html_template.render(context, request))

@login_required(login_url="/login/")
def index(request):
    context = {}
    context['segment'] = 'index'

    html_template = loader.get_template('index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]
        context['segment'] = load_template

        html_template = loader.get_template(load_template)
        return HttpResponse(html_template.render(context, request))

    except TemplateDoesNotExist:

        html_template = loader.get_template('page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('page-500.html')
        return HttpResponse(html_template.render(context, request))
