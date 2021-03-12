from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from constants import JSON_AUTH


class GoogleCalendarGatherer:
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 50 events on the user's calendar.
    """
    # If modifying these scopes, delete the file token.pickle.
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

    def __init__(self, url, credentials):
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        creds = None
        if os.path.exists('../token.pickle'):
            with open('../token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials[JSON_AUTH], self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('../token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        self.service = build('calendar', 'v3', credentials=creds)

    def parse_request(self, request_type, events):
        output = []
        for request in events[1]:
            name = events[0].replace('.', '#')
            output.append({name: [request['kind'], request['status'],
                                  request['created'], request['summary'],
                                  request['creator'], request['organizer'],
                                  request['start'], request['end']]})
        return output

    def request(self):
        # Call the Calendar API
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print('Getting the upcoming 50 events')
        calendars = self.service.calendarList().list().execute()
        calendar_types = calendars.get('items', [])
        calendar_types = [calendar['id'] for calendar in calendar_types]
        all_events = []
        for calendar_name in calendar_types:
            events_result = self.service.events().list(calendarId=calendar_name,
                                                       timeMin=now,
                                                       maxResults=10,
                                                       singleEvents=True,
                                                       orderBy='startTime').execute()
            events = events_result.get('items', '')
            if not events:
                print('No upcoming events found.')
            all_events.append((calendar_name, events))
            # for event in events:
            #     start = event['start'].get('dateTime', event['start'].get('date'))
            #     print(start, event['summary'])
        return {"calendar_events": all_events}
