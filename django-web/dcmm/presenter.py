from datetime import datetime
from enum import Enum
import json
import os
import re
import requests
from django.http import HttpResponse, Http404
from allauth.socialaccount.models import SocialToken, SocialAccount
from dcmm_gatherer.database_manipulator import DatabaseManipulator
import pandas as pd
# Custom form
from . import forms
# Celery Task
from .tasks import ProcessDownload


class DCMM_Labels(Enum):
    NewComponentOrCapability = 0
    Improvement = 1
    Check = 2
    Modification = 3


class Presenter:
    GRAPH_TYPES = ['pie', 'bar', 'bubble']

    def __init__(self, request):
        self.request = request
        self.repositories = {}
        self.predictions = {}
        self.connections = {}
        self.milestones = {}
        self.db = None
        # Get social account username
        self.user_data = SocialAccount.objects.filter(user=self.request.user)[0]
        # Github form
        self.form = None
        self.task_id = 0

    def set_database_connection(self):
        # Make query to database and retrieve all information
        nosql_username = os.environ.get('MONGO_INITDB_ROOT_USERNAME', 'user')
        nosql_password = os.environ.get('MONGO_INITDB_ROOT_PASSWORD',
                                        'extrastrongpass')
        self.db = DatabaseManipulator({}, nosql_username, nosql_password)

    def get_post_data(self, data_len):
        if self.request.method == "POST":
            data = dict(self.request.POST)
            if len(data) == data_len:
                error = "No repository was selected"
                return error
            return data
        return None

    def get_connections_dataframe(self):
        return self.connections

    def get_dataframe(self):
        # Create dataframe from gathered data
        labels = []
        number_of_labels = []
        graphs_types = []
        for graph_type in self.GRAPH_TYPES:
            for key, value in self.predictions.items():
                match = re.search(r'\..*', str(DCMM_Labels(int(key))))
                label = match.group(0)[1:]
                labels.append(label)
                number_of_labels.append(value)
                graphs_types.append(graph_type)
        dataframe = {'Labels': labels, 'Count_labels': number_of_labels,
                     'Graph_type': graphs_types}
        return pd.DataFrame(data=dataframe), self.connections, self.milestones

    def _get_repository_name(self, entity, selected_repositories):
        if not entity['labels']:
            return
        match = re.search(r'(?<=repos).*(?=labels)',
                          entity['labels'][0]['url'])
        striped = match.group(0)[1:-1]
        if striped in selected_repositories:
            return striped
        # Set repository to 0
        self.repositories[striped] = 0

    def _fill_connections(self, entity, selected_repository_name):
        if selected_repository_name:
            login = entity['user']['login']
            if 'title' in entity and 'number' in entity and \
                    login not in self.connections:
                self.connections[login] = {'titles': [entity['title']],
                                           'issue_number': [entity['number']]}
            elif 'title' in entity and 'number' in entity:
                self.connections[login]['titles'].append(entity['title'])
                self.connections[login]['issue_number'].append(entity['number'])

    def _fill_milestones(self, entity, selected_repository_name):
        if selected_repository_name:
            if 'milestone' in entity and entity['milestone']:
                milestone_title = entity['milestone']['title']
            else:
                # No milestones present, end filling
                return False
            # Otherwise continue in filling milestones
            if 'title' in entity and milestone_title not in self.milestones:
                milestone_creator = entity['milestone']['creator']['login']
                self.milestones[milestone_title] = {'title': [entity['title']],
                                                    'creator': milestone_creator,
                                                    'open_issues': entity['milestone']['open_issues']}
            elif 'title' in entity and 'milestone' in entity and \
                    entity['milestone']:
                self.milestones[milestone_title]['title'].append(entity['title'])

    def _fill_predictions(self, entity, selected_repository_name):
        if selected_repository_name:
            self.repositories[selected_repository_name] = 0
            if 'predicted' in entity:
                if str(entity['predicted']) in self.predictions:
                    self.predictions[str(entity['predicted'])] += 1
                else:
                    self.predictions[str(entity['predicted'])] = 1

    def filter_database_data(self):
        # Get data that were selected by user
        selected_data = self.get_post_data(2)
        # Filter data based on the input date
        if selected_data and 'date' in selected_data:
            date = datetime.strptime(selected_data['date'][0], "%m/%d/%Y")
            _, filtered_data = self.db.get_data(date=date)
        else:
            # Otherwise gather all the data
            _, filtered_data = self.db.get_data()
        return selected_data, filtered_data

    def visualise(self):
        if not self.db.collections:
            # Update collections
            self.db.collections.append(
                    self.db.client["DCMMDatabase"]['Github' + self.user_data.extra_data['login']])
            self.db.collections.append(self.db.client["DCMMDatabase"]['Jira'])
        selected_data, filtered_data = self.filter_database_data()
        selected_repositories = []
        if selected_data and 'repositories' in selected_data:
            selected_repositories = selected_data['repositories']
        for entity in filtered_data:
            if self.request.method == "POST" and 'labels' in entity:
                repo_name = self._get_repository_name(entity,
                                                      selected_repositories)
                self._fill_predictions(entity, repo_name)
                self._fill_connections(entity, repo_name)
                self._fill_milestones(entity, repo_name)
            elif self.request.method == "GET" and 'labels' in entity:
                self._get_repository_name(entity, selected_repositories)
        if self.request.method == "GET":
            return False
        return True

    def connect_github(self):
        query = SocialToken.objects.filter(account__user=self.request.user,
                                           account__provider='github')
        token = None
        if query:
            token = query[0]
            print(token)
            headers = {'Authorization': 'token ' + str(token)}
            repos = requests.get('https://api.github.com/user/repos',
                                 headers=headers)
            content = list(
                    element['full_name'] for element in json.loads(repos.text))
            self.form = forms.GithubForm(content)
        return token

    def gathering(self):
        token = self.connect_github()
        data = self.get_post_data(1)
        if data:
            if isinstance(data, str):
                return data
            # Create Task
            nosql_username = os.environ.get('MONGO_INITDB_ROOT_USERNAME',
                                            'user')
            nosql_password = os.environ.get('MONGO_INITDB_ROOT_PASSWORD',
                                            'extrastrongpass')
            download_task = ProcessDownload.delay(data, str(token),
                                                  self.user_data.extra_data['login'],
                                                  nosql_username,
                                                  nosql_password)
            # Get ID
            self.task_id = download_task.task_id
        return False

    def download_tables(self):
        response = HttpResponse(self.connections,
                                content_type="application/json")
        return response
