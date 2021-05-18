from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse
from django.template import loader, TemplateDoesNotExist
from django_plotly_dash import DjangoDash
from allauth.socialaccount.models import SocialAccount

from .forms import ToDoForm
# Dashboard
from .dashboard import setup_layout, register_callbacks
from .presenter import Presenter


@login_required(login_url="/login/")
def gathering(request):
    presenter = Presenter(request)
    data = presenter.gathering()
    if isinstance(data, str):
        return render(request, 'gathering.html', {'form': presenter.form,
                                                  'error': data})
    # GET method was called, render page without task_id
    if data:
        return render(request, 'gathering.html', context={'form': presenter.form})
    # Return demo view with Task ID, POST method involved
    return render(request, 'gathering.html', {'form': presenter.form,
                                              'task_id': presenter.task_id})


def create_datepicker_from(request):
    user_form = ToDoForm()
    return {'form': user_form}


@login_required(login_url="/login/")
def visualisations(request):
    presenter = Presenter(request)
    context = create_datepicker_from(request)
    presenter.set_database_connection()
    # Visualise either empty web page or web page
    # with selected repositories charts
    is_post = presenter.visualise()
    if not is_post:
        context['repositories'] = enumerate(presenter.repositories.keys())
        return render(request, 'visualisations.html', context=context)
    # Get post data, when not present method return error
    data = presenter.get_post_data(2)
    if isinstance(data, str):
        # Setup context for rendering visualisations html
        context['repositories'] = enumerate(presenter.repositories.keys())
        context['error'] = data
        return render(request, 'visualisations.html', context)
    # Setup django dash and plotly for graph showing
    app = DjangoDash('SimpleExample')  # replaces dash.Dash
    app = setup_layout(app)
    # Create pandas dataframe for visualisations
    dataframe, connections, milestones = presenter.get_dataframe()
    app = register_callbacks(app, dataframe, connections, milestones)
    # Setup context
    context['repositories'] = enumerate(presenter.repositories.keys())
    context['predictions'] = True
    # Export tables of DCMM
    if 'tables' in data:
        context['tables'] = presenter.download_tables()
        return render(request, 'tables.html', context=context)
                               # ?username=' + presenter.user_data.extra_data['login'], context=context)
    return render(request, 'visualisations.html', context=context)


@login_required(login_url="/login/")
def tables(request, username):
    user_data = SocialAccount.objects.filter(user=request.user)[0]
    if username == user_data.extra_data['login']:
        return render(request, 'tables.html')

    load_template = request.path.split('/')[-1]
    context = {'segment': load_template}
    html_template = loader.get_template('page-404.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def settings(request):
    context = {'segment': 'settings'}
    html_template = loader.get_template('settings.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def index(request):
    presenter = Presenter(request)
    presenter.set_database_connection()
    # Visualise either empty web page or web page
    # with selected repositories charts
    presenter.visualise()
    context = {'Metrics': presenter.metrics}
    return render(request, 'index.html', context=context)


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
