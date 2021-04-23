# Celery
from celery import shared_task
# Celery-progress
from celery_progress.backend import ProgressRecorder
# import application
from dcmm_gatherer import classification_scheduler


def execute_gathering_process(username, data, token,
                              nosql_username, nosql_password):
    joined = ' '.join(data['repositories'])
    classification_scheduler.main(['--github-username', username,
                                   '--repositories', joined],
                                  token_authentication_github=token,
                                  nosql_username=nosql_username,
                                  nosql_password=nosql_password)


# Celery Task
@shared_task(bind=True)
def ProcessDownload(self, data, token, username, nosql_username, nosql_password):
    # Create the progress recorder instance
    # which we'll use to update the web page
    progress_recorder = ProgressRecorder(self)

    for i in range(1):
        execute_gathering_process(username, data, str(token),
                                  nosql_username, nosql_password)
        # Update progress on the web page
        progress_recorder.set_progress(i, 1, description="Gathering data")
    return 'Task Complete'