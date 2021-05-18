import numpy
import pickle
from constants import COMMON_ISSUE_TYPES


class MLModel:
    DESCRIPTION_FIELD = 'description'
    LABEL_FIELD = 'labels'

    def __init__(self, model_cursor, input_data=None, uid=None):
        uid = uid
        self.model = None
        self.vectorizer = None
        self.tfidf_transformer = None
        self.test_description = []
        self.issue_types = []
        self.integer_labels = []
        for model in model_cursor:
            if uid:
                if model['model'] == uid:
                    self._retrieve_ml_database(model, model_cursor)
                    break
            else:
                self._retrieve_ml_database(model, model_cursor)
                break
        # Setup input data that were gathered trough APIs of selected tools
        _, self.input_data = input_data
        if input_data:
            self.input_data = self._prepare_data(input_data)

    @staticmethod
    def issue_converter(value):
        """
        Convert issue type field (github) in csv to issue type without whitespaces,
        'kind' forewords to be compatible with naming from Jira.
        :param value: Issue Type field that is being processed.
        :return processed Issue Type field value.
        :rtype: str.
        """
        splitted = value.split(';')
        for split in splitted:
            for issue_type_key, issue_type_values in COMMON_ISSUE_TYPES.items():
                if any(issue_type in split.upper() for issue_type in
                       issue_type_values):
                    return issue_type_key
                else:
                    # No kind is specified, so it is custom label
                    value = numpy.nan
        return value

    @property
    def labels(self):
        """ Return labels based on the converted input labels which are
            compared against trained model labels. It uses external funcitonality
            that is implemented in dataset_preparation file which is executed
            as external tool.
        :return: Numpy array tha contains issue type number that is
                 associated with model issue type number.
        :rtype numpy.array(issue_type_number)
        """
        return numpy.array(self.integer_labels)

    def _retrieve_ml_database(self, model, cursor):
        """ Retrieve machine learning objects from database that are needed
            for the prediction or scoring of the gathered input against model.
        :param model: Machine learning model that is stored in mongoDB.
        :param cursor: mongoDB cursor pointing on Machine learning model.
                       Database contains from this cursor position on next
                       position in database Vectorizer class and on 3th position
                       TfIdfTransformer class.
        """
        self.model = pickle.loads(model['binary_field'])
        model = cursor.next()
        self.vectorizer = pickle.loads(model['binary_field'])
        model = cursor.next()
        self.tfidf_transformer = pickle.loads(model['binary_field'])

    def _prepare_data(self, input_data):
        """ Prepare input data that are gathered from database and filled in
            machine learning model. These data are stored in appropriate lists
            where important information for machine learning are found.
        :return transformed Description fields from different Gathering Services
                (e.g JiraGatherer, GithubGatherer etc.)
        :rtype: numpy.array(transformed strings by vectorizer and tfidftransformation)
        """
        for data in input_data[1]:
            if self.DESCRIPTION_FIELD in data:
                if self.LABEL_FIELD in data and data[self.LABEL_FIELD]:
                    # Convert issue type, if not labeled mean value cannot
                    # be evaluated in predicted
                    for label in data[self.LABEL_FIELD]:
                        # fixme: add to show current mean value
                        item = self.issue_converter(label['name'])
                        # item = label['name']
                        if not isinstance(item, str) and numpy.isnan(item):
                            continue
                        # Check available types
                        for index, issue_key in enumerate(COMMON_ISSUE_TYPES
                                                          .keys()):
                            # fixme: add to show current mean value
                            if item == issue_key:

                                # Append to all temporary fields issues, labels
                                # and integer labels. Integer labels are used for mean value
                                self.integer_labels = numpy.append(self.integer_labels,
                                                                   int(index))
                                self.issue_types.append(item)
                                self.test_description.append(data[self.DESCRIPTION_FIELD])
                        # One item can have only one label,
                        # break the loop over all of the labels
                        break
        get_description = numpy.array(self.test_description)
        x_samples = self.vectorizer.transform(get_description)
        try:
            x_samples_tf = self.tfidf_transformer.transform(x_samples)
        except ValueError:
            x_samples_tf = []
        return x_samples_tf

    def score(self, X_test, Y_test):
        result = self.model.score(X_test, Y_test)
        return result

    def predict(self, samples=None):
        """ Predict function of machine learning model that was collected from mongoDB.
        :return: predicted labels based on the description strings.
        :rtype: list(int)
        """
        if samples:
            result = self.model.predict(samples)
        else:
            try:
                result = self.model.predict(self.input_data)
            except ValueError:
                print("Input data are missing or in incorrect shape. "
                      "Check whether you provide correct repository name.")
                raise
        return result
