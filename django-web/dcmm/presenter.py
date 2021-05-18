from datetime import datetime, timedelta
from enum import Enum
import json
import os
import re
import requests
from django.http import HttpResponse, Http404
from allauth.socialaccount.models import SocialToken, SocialAccount
from dcmm_gatherer.database_manipulator import DatabaseManipulator
from dcmm_gatherer.ml_model import MLModel
import pandas as pd
import itertools
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
        self.metrics = {}
        self.db = None
        # Get social account username
        self.user_data = None
        # Github form
        self.form = None
        self.task_id = 0
        self._repository_issues = {}

    def check_issues_by_repository(self, repository, entity):
        if not repository:
            return
        if repository in self._repository_issues:
            try:
                if entity['labels']:
                    self._repository_issues[repository + 'labels'].append(entity)
                self._repository_issues[repository].append(entity)
            except KeyError:
                return
        else:
            if entity['labels']:
                self._repository_issues[repository + 'labels'] = [entity]
            self._repository_issues[repository] = [entity]

    def set_database_connection(self):
        try:
            self.user_data = SocialAccount.objects.filter(user=self.request.user)[0]
        except IndexError:
            pass
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

    def _get_repository_name(self, entity, selected_repositories, check_labels=True):
        if check_labels:
            if not entity['labels']:
                return
            match = re.search(r'(?<=repos).*(?=labels)',
                              entity['labels'][0]['url'])
            striped = match.group(0)[1:-1]

            if striped in selected_repositories:
                return striped
            # Set repository to 0
            self.repositories[striped] = 0
        else:
            match = re.search(r'(?<=repos).*(?=issues)',
                              entity['comments_url'])
            striped = match.group(0)[1:-1]
            return striped

    def _get_label(self, entity):
        label = [MLModel.issue_converter(filter_kind['name'])
                 for filter_kind in entity['labels']]
        # Filter nan values
        label = [item for item in label if isinstance(item, str)]
        # When no value is present, set None as default label
        if not label:
            label = ['None']
        return label

    def _compute_time_delta(self):
        if not 'TimeConsumption' in self.metrics:
            return False
        if len(self.metrics['TimeConsumption']) > 500:
            consumption_delta = sum([date for date in
                                     self.metrics['TimeConsumption'][:500]],
                                    timedelta()) / len(self.metrics['TimeConsumption'][:500])
        else:
            consumption_delta = sum([date for date in
                                     self.metrics['TimeConsumption']],
                                    timedelta() / len(self.metrics['TimeConsumption']))
        d = {"days": consumption_delta.days}
        d["hours"], rem = divmod(consumption_delta.seconds, 3600)
        d["minutes"], d["seconds"] = divmod(rem, 60)
        self.metrics['TimeConsumption'] = "days: {}, hours:{}, minutes{} and seconds:{}"\
            .format(d['days'], d['hours'], d['minutes'], d['seconds'])

        # Sort TimeResources of top ten contributors for issues.
        out = {k: len(v) for k, v in sorted(self.metrics['TimeResources'].items(),
                                       key=lambda item: len(item[1]), reverse=True)}
        self.metrics['TimeResources'] = dict(itertools.islice(out.items(), 10))

    def _get_metrics(self, entity):
        if 'TimeResources' in self.metrics and \
           'TimeConsumption' in self.metrics:
            if 'created_at' in entity and entity['created_at'] and \
               'updated_at' in entity and entity['updated_at']:
                created_date = datetime.strptime(entity['created_at'],
                                              "%Y-%m-%dT%H:%M:%SZ")
                # Check human resources
                if entity['user']['login'] in self.metrics['TimeResources'] and\
                   created_date not in self.metrics['TimeResources'][entity['user']['login']]:
                    self.metrics['TimeResources']\
                                [entity['user']['login']].append(created_date)
                else:
                    self.metrics['TimeResources'][entity['user']['login']] = [created_date]
                # Check average time consumption
                updated_date = datetime.strptime(entity['updated_at'],
                                              "%Y-%m-%dT%H:%M:%SZ")
                final_date = updated_date - created_date
                self.metrics['TimeConsumption'].append(final_date)
        else:
            if 'created_at' in entity and entity['created_at'] and \
               'updated_at' in entity and entity['updated_at']:
                created_date = datetime.strptime(entity['created_at'],
                                              "%Y-%m-%dT%H:%M:%SZ")
                # Check human resources
                self.metrics['TimeResources'] = {entity['user']['login']: [created_date]}
                updated_date = datetime.strptime(entity['updated_at'],
                                              "%Y-%m-%dT%H:%M:%SZ")
                self.metrics['TimeConsumption'] = [updated_date - created_date]

    def _fill_visualisations(self, entity, selected_repository_name):
        if selected_repository_name:
            self._fill_predictions(entity, selected_repository_name)
            self._fill_connections(entity)
            self._fill_milestones(entity)

    def _fill_connections(self, entity):
        login = entity['user']['login']
        if 'title' in entity and 'number' in entity and \
                login not in self.connections:
            self.connections[login] = {'titles': [entity['title']],
                                       'issue_number': [entity['number']]}
        elif 'title' in entity and 'number' in entity:
            self.connections[login]['titles'].append(entity['title'])
            self.connections[login]['issue_number'].append(entity['number'])

    def _fill_milestones(self, entity):
        if 'milestone' in entity and entity['milestone']:
            milestone_title = entity['milestone']['title']
        elif 'state' in entity and entity['state'] != "open":
            # Issue is already closed
            return False
        else:
            # No milestones present, end filling
            return False
        # Otherwise continue in filling milestones
        if 'title' in entity and milestone_title not in self.milestones:
            milestone_creator = entity['milestone']['creator']['login']
            label = self._get_label(entity)
            self.milestones[milestone_title] = {'title': [entity['title']],
                                                'label': label,
                                                'creator': milestone_creator,
                                                'open_issues': entity['milestone']['open_issues']}
        elif 'title' in entity and 'milestone' in entity and \
                entity['milestone']:
            label = self._get_label(entity)
            if entity['title'] not in self.milestones[milestone_title]['title']:
                self.milestones[milestone_title]['title'].append(entity['title'])
                # Add label
                self.milestones[milestone_title]['label'].append(label[0])

    def _fill_predictions(self, entity, selected_repository_name):
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
        if not self.db.collections and self.user_data:
            # Update collections
            self.db.collections.append(
                    self.db.client["DCMMDatabase"]['Github' + self.user_data.extra_data['login']])
            self.db.collections.append(self.db.client["DCMMDatabase"]['Jira'])
        selected_data, filtered_data = self.filter_database_data()
        selected_repositories = []
        if selected_data and 'repositories' in selected_data:
            selected_repositories = selected_data['repositories']
        for entity in filtered_data:
            if self.request.method == "POST":
                repo_name = self._get_repository_name(entity,
                                                      selected_repositories,
                                                      False)
                self.check_issues_by_repository(repo_name, entity)
            if self.request.method == "POST" and 'labels' in entity:
                repo_name = self._get_repository_name(entity,
                                                      selected_repositories)
                self._fill_visualisations(entity, repo_name)
            elif self.request.method == "GET" and 'labels' in entity:
                self._get_metrics(entity)
                self._get_repository_name(entity, selected_repositories)
        self._compute_time_delta()
        if self.request.method == "GET":
            return False
        return True

    def connect_github(self):
        query = SocialToken.objects.filter(account__user=self.request.user,
                                           account__provider='github')
        token = None
        if query:
            token = query[0]
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
