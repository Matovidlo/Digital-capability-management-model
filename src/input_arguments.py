import argparse


class DCMMArguments(argparse.ArgumentParser):
    def __init__(self):
        """ Initialize path arguments """
        super(DCMMArguments, self).__init__(prog="DCMM API gatherer",
                                            description="Gathering tool for "
                                                        "gathering DCMM activities "
                                                        "from various sources "
                                                        "using APIs of the tools.")
        self.add_argument('--github-username',
                          help='Username that is supplied to API tools where '
                               'user credentials are mandatory. The pasword '
                               'or token is part of the separate reading process')
        self.add_argument('--jira-username',
                          help='Username that is supplied to API tools where '
                               'user credentials are mandatory. The pasword '
                               'or token is part of the separate reading process')
        self.add_argument('--google-credentials-json',
                          help='Path to credentials.json file to connect to '
                               'GoogleCalendar API which is mandatory in order '
                               'to gather information from calendar.')
        self.add_argument('--token-authentication-github', action='store_true',
                          help='When present, token is required as authentication '
                               'cannot proceede without token.')
        self.add_argument('--password-authentication-jira', action='store_true',
                          help='When present, password authentication is required '
                               'by jira and user supplies the password when '
                               'this option is set to true.')
        self.args = self.parse_args()
        # if self.args.input is None and self.args.list_filters is False:
        #     self.error("--input parameter required. No input file "
        #                "was chosen.")
