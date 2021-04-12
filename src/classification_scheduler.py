import getpass
import urllib3
import numpy
from input_arguments import DCMMArguments
from API_communicator import APICommunicator
from constants import TOKEN_AUTH, USER_AUTH, JSON_AUTH, gathering_urls,\
    GITHUB, JIRA, GOOGLE_CALENDAR, TRELLO, GITHUB_API
from database_manipulator import DatabaseManipulator
from ml_model import MLModel


if __name__ == '__main__':
    cmdline_arguments = DCMMArguments().args
    headers = None
    # Github credentials
    github_username = cmdline_arguments.github_username
    github_token = None
    # Jira credentials
    jira_username = cmdline_arguments.jira_username
    jira_password = None
    # Nosql credentials
    nosql_username = None
    nosql_password = None
    if cmdline_arguments.token_authentication_github:
        github_token = getpass.getpass(prompt="Please provide github "
                                              "authorization token "
                                              "for accessing API.")
    if cmdline_arguments.password_authentication_jira:
        jira_password = getpass.getpass(prompt="Please provide jira "
                                               "password for accessing API.")
    if cmdline_arguments.nosql_username:
        nosql_username = input("Specify username for nosql database:")
    if cmdline_arguments.nosql_password:
        nosql_password = getpass.getpass(prompt="Provide password for nosql database:")
    for key, url in gathering_urls.items():
        new_url = url
        if key is JIRA and USER_AUTH in url[1]:
            # Add user authentication to JIRA gathering url
            new_url = [url[0], {USER_AUTH: ['', '', '']}]
            new_url[1][USER_AUTH][0] = \
                url[1][USER_AUTH][0].format(username=jira_username)
            new_url[1][USER_AUTH][1] = \
                url[1][USER_AUTH][1].format(password=jira_password)
        elif key is GOOGLE_CALENDAR and JSON_AUTH in url[1]:
            # Add credentials to GC gathering urls
            new_url = [url[0],
                       {JSON_AUTH: [url[1][JSON_AUTH][0]
                                    .format(file_path=cmdline_arguments
                                            .google_credentials_json), '']}]
        elif key is GITHUB and USER_AUTH in url[1]:
            new_url = [GITHUB_API + repository for repository in cmdline_arguments.repositories]
            new_url = [new_url, {USER_AUTH: ['', '', '']}]
            new_url[1][USER_AUTH][2] = \
                urllib3.make_headers(user_agent="python-urllib3/1.25.11",
                                     basic_auth=github_username + ':' +
                                                github_token)
        elif key is TRELLO:
            new_url = url
        # Update gathering_url when new information added
        gathering_urls[key] = new_url
    api_communicator = APICommunicator(gathering_urls)
    api_communicator.gather_resources()
    # Database Manipulator could be inside API communicator
    db = DatabaseManipulator(gathering_urls, nosql_username, nosql_password)
    api_communicator.create_transactions(db)
    machine_learning_model = MLModel(db.model_cursor, db.get_data())
    # Predict DCMM entities from gathered API input
    prediction = machine_learning_model.predict()
    for desc, category in zip(machine_learning_model.test_description, prediction):
        if category == 0:
            print('{} => New feature'.format(desc))
        elif category == 1:
            print('{} => Improvement'.format(desc))
        elif category == 2:
            print('{} => Bug'.format(desc))
    mean_value = numpy.mean(prediction == machine_learning_model.labels)
    print(mean_value)