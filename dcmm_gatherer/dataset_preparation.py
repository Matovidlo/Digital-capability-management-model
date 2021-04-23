import re
import pandas as pd
import matplotlib
from matplotlib.cm import tab10
import matplotlib.pyplot as plt
import numpy
from sklearn.feature_extraction.text import TfidfTransformer, TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import metrics
# Sklearn models
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import MultinomialNB
# This is used for graphical representation of gathered data
import pickle
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from umap import UMAP
import umap.plot as uplt

def plot_history(history):
    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']
    x = range(1, len(acc) + 1)

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(x, acc, 'b', label='Training acc')
    plt.plot(x, val_acc, 'r', label='Validation acc')
    plt.title('Training and validation accuracy')
    plt.legend()
    plt.subplot(1, 2, 2)
    plt.plot(x, loss, 'b', label='Training loss')
    plt.plot(x, val_loss, 'r', label='Validation loss')
    plt.title('Training and validation loss')
    plt.legend()
    plt.show()


def description_converter(value):
    # Remove https links
    value = re.sub(r'https?:\/\/.*\]', '', value)
    # Remove https links
    value = re.sub(r'https?:\/\/.*\n', '', value)
    # Remove https links
    value = re.sub(r'https?:\/\/.*', '', value)
    # Filter debug output of the execution
    value = re.sub(r'\[?[A-Z]+[- ]\d+\]?', '', value, flags=re.MULTILINE)
    # todo:
    #  This regex is for org. exceptions (org[\s\S]+errors)
    # Remove html tags
    # value = re.sub(r'<.*\/>\n', '', value, flags=re.S)
    # Remove code segments
    value = re.sub(r'^\{code((\||\s|:|=|\.|\#)?(\(.*\))?(\w+|\d+)?)+\}[\s\S]*?\{code\}',
                   '', value, flags=re.MULTILINE)
    # todo: is it necessary to remove quote segment? They just highlight
    # Remove quote segments
    value = re.sub(r'^\{quote((\||\s|:|=|\.|\#)?(\(.*\))?(\w+|\d+)?)+\}[\s\S]*?\{quote\}',
                   '', value, flags=re.MULTILINE)
    # Remove noformat segments
    value = re.sub(
        r'^\{noformat((\||\s|:|=|\.|\#)?(\(.*\))?(\w+|\d+)?)+\}[\s\S]*?\{noformat\}',
        '', value, flags=re.MULTILINE)
    # Remove xml tags
    # value = re.sub(r'<\w+>.*<\/\w+>\n', '', value, flags=re.S)
    # At reports from scala removed
    value = re.sub(r'(\s)?at (\w+\S+)\(.*\.\w+:\d+\)\n', '', value)
    # Filter datetimes from output. It is necessary since date does not influence
    # training in positive but rather negative way.
    value = re.sub(r'((\d{4})-(\d{2})-(\d{2})|'
                   r'(\d{4})\/(\d{2})\/(\d{2}))'
                   r' (\d{2}):(\d{2}):(\d{2})(\.\d+)?', '', value)
    value = re.sub(r'\{[\s\S]*?\}', '', value)
    value = re.sub(r'<!--[\s\S]*?-->', '', value)
    value = re.sub(r'```[\s\S]*?```', '', value)
    # value = re.sub(r'(?<=(info|error|Exception))(\s+(\(|\[)((\w+|\d+)(-|\.|_|=|\]|\)|,\s|\s))*)*',
    #                '', value)
    value = re.sub(r'\((\d+(,)?(\s)?(\)\.\.\.)?)+', '', value)
    # Remove github markdown issuing steps
    value = re.sub(r'\*\*(\w+(\s|:|\/|\'|\!))*(\w+)?', '', value)
    value = ' '.join(value.split())
    if not value or len(value.split()) < 20:
        return numpy.nan
    return value


common_issue_types = {'New Feature': ['FEATURE', 'NEW-FEATURE', 'NEW_FEATURE', 'NEW FEATURE'],
                      'Improvement': ['ENHANCEMENT', 'IMPROVEMENT', 'DOC', 'DOCUMENTATION'],
                      'Test': ['TEST'],
                      'Bug': ['BUG'],}

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
        for issue_type_key, issue_type_values in common_issue_types.items():
            if any(issue_type in split.upper() for issue_type in issue_type_values):
                return issue_type_key
            else:
                # No kind is specified, so it is custom label
                value = numpy.nan
    return value

def read_csv_file(filepath, mandatory_fields, optional_fields):
    """
    Read csv file with all fields. When some of the optional fields
    are missing try to read it without them. This way parsing allows to have more
    accurate machine learning models to be built.
    :param filepath: path to file where csv is located.
    :param mandatory_fields: Mandatory column fields of csv file.
    :param optional_fields: Optional column fields that could be present in csv.
                            Different projects and issues varies from company
                            to company and from platform to another one.
                            E.g github is quite different in comparison with Jira.
    :return : read pandas Dataframe that contains mandatory fields and some of the
              optional ones. This dataframe is used in machine learning process.
    :rtype: cls:pandas:Dataframe.
    """
    fields = mandatory_fields + optional_fields
    try:
        df = pd.read_csv(filepath, usecols=fields,
                         header=0, sep=',', dtype={'Description': str},
                         encoding='utf-8',
                         converters={#'Description': description_converter,
                                     'Issue Type': issue_converter})
    except ValueError as ex:
        for field in optional_fields:
            if field in ex.args[0]:
                optional_fields.remove(field)
                break
        df = read_csv_file(filepath, mandatory_fields, optional_fields)
    return df

filepath_dict = {'kafka-newfeatures': 'dataset/kafka_newfeatures.csv',
                 'mongodb-newfeatures': 'dataset/mongodb_server_newfeatures.csv',
                 'jfrog-artifactory-newfeatures': 'dataset/jfrog_artifactory_bin_repo_newfeatures.csv',
                 'ovirt-newfeatures': 'dataset/ovirt_newfeatures.csv',
                 'sakai-feature-requests': 'dataset/sakai_feature_requests.csv',
                 'jfrog-artifactory-improvements': 'dataset/jfrog_artifactory_bin_repo_improvements.csv',
                 'mongodb-improvements': 'dataset/mongodb_server_improvements.csv',
                 #'apache-mapreduce-improvements': 'dataset/mapreduce_improvements1000.csv',
                 # 'netbeans-improvements': 'dataset/netbeans_1000_improvements_and_newfeatures.csv',
                 'kafka-tests': 'dataset/kafka_tests.csv',
                 'hadoop-tests': 'dataset/hadoop_tests.csv',
                 # Smaller jira projects consisting of tests
                 'hadoop-hdfs-tests': 'dataset/apache_hadoop_hdfs_tests.csv',
                 'hbase-tests': 'dataset/apache_hbase_tests.csv',
                 'hive-tests': 'dataset/apache_hive_tests.csv',
                 'ignite-tests': 'dataset/apache_ignite_tests.csv',
                 'lucene-tests': 'dataset/apache_lucene_tests.csv',
                 'solr-tests': 'dataset/apache_solr_tests.csv',
                 'apache-spark-tests': 'dataset/apache_spark_tests.csv',

                 #'bug-jfrog-artifactory': 'dataset/jfrog_artifactory_bin_repo_bugs.csv',
                 'bug-hadoop': 'dataset/hadoop_bugs1000.csv',
                 'bug-kafka': 'dataset/kafka_bugs1000.csv',
                 'bug-maven': 'dataset/bug_maven1000.csv',
                 #'bug-netbeans': 'dataset/netbeans_bug1000.csv',
                 'github-docker-compose': 'dataset/github/compose.csv',
                 'github-velero': 'dataset/github/velero.csv',
                 'github-nodejs': 'dataset/github/node.csv',
                 'github-superset': 'dataset/github/superset.csv',
                 'github-vue': 'dataset/github/vue.csv',
                 'github-ohmyzsh': 'dataset/github/ohmyzsh.csv',
                 'github-tensorflow': 'dataset/github/tensorflow.csv',
                 'github-bootstrap': 'dataset/github/bootstrap.csv',
                 'github-vscode': 'dataset/github/vscode.csv',
                 'github-kubernetes': 'dataset/github/kubernetes.csv',
                 'github-go': 'dataset/github/go.csv',
                 }
test_sentences = {'puppeteer': 'dataset/github/puppeteer.csv',
                  'nodejs': 'dataset/github/node.csv',
                  'superset': 'dataset/github/superset.csv',
                  'vue': 'dataset/github/vue.csv',
                  'kubernetes': 'dataset/github/kubernetes.csv'}


if __name__ == '__main__':
    df_list = []
    # Setup mandatory and optional fields.
    mandatory_fields = ['Created', 'Creator', 'Description', 'Resolution', 'Status',
                        'Summary', 'Issue Type']
    optional_fields = ['Assignee', 'Labels', 'Resolved',
                       'Outward issue link (Blocker)']
    # Iterate over all of the filepaths with sources. Parse csv in the path
    for source, filepath in filepath_dict.items():
        # todo: use multiple inputs in machine learning
        df = read_csv_file(filepath, mandatory_fields, optional_fields)
        df.dropna(subset=['Description'], inplace=True)
        df['source'] = source  # Add another column filled with the source name
        # Filter data frame based on the Issue Type values
        df = df.loc[df['Issue Type'].isin(['Bug', 'New Feature', 'Improvement',
                                           'Test', 'Question'])]
        df_list.append(df)
    # Concatenate all the dataframes to single pandas Dataframe.
    df = pd.concat(df_list)
    # Create categories based on the Issue Type using factorization (transformation
    # of unique fields into numbers 0 to n). This is used in machine learning process.
    df['category_id'], uniques = df['Issue Type'].factorize()

    # Do not split dataset
    # df_kafka_newcapabilities = df[df['source'] == 'kafka']

    sentences = df['Description'].values
    labels = df['category_id'].values
    # Change test size that is used to check the accuracy of the built model
    # If it is too trained on dataset it is problem.
    sentences_train, sentences_test, y_train, y_test = \
        train_test_split(sentences, labels, test_size=0.10, random_state=650)

    # Real repository examples
    # Add test senteces of puppeteer github
    testing_array = []
    y_test = []
    for test_repository in test_sentences.values():
        sentences_test = pd.read_csv(test_repository,
                                     usecols=['Description', 'Issue Type'],
                                     encoding='utf-8',
                                     converters={'Description':
                                                 description_converter,
                                                 'Issue Type':
                                                 issue_converter})
        # Remove all test sentences that does not contain issue type
        sentences_test.dropna(subset=['Issue Type'], inplace=True)
        # Remove from the rest of sentences that ones that are missing description.
        sentences_test.dropna(subset=['Description'], inplace=True)
        for item in sentences_test['Issue Type']:
            for index, issue_key in enumerate(common_issue_types.keys()):
                if item == issue_key:
                    y_test = numpy.append(y_test, int(index))
        sentences_test = numpy.array(sentences_test['Description'])
        testing_array = numpy.append(testing_array, sentences_test)
    # Scikit learn vectorizer
    vectorizer = CountVectorizer()
    vectorizer.fit(sentences_train)
    x_train_counts = vectorizer.fit_transform(sentences)
    print(x_train_counts.shape)

    # Count frequencies instead of occurences
    tf_transformer = TfidfTransformer()
    x_train_tf = tf_transformer.fit_transform(x_train_counts)
    print(x_train_tf.shape)

    # clf = MultinomialNB().fit(x_train_tf, labels)
    clf = SGDClassifier(loss='hinge', penalty='l2', alpha=0.0001, random_state=48,
                        max_iter=1200, tol=None).fit(x_train_tf, labels)
    x_samples = vectorizer.transform(testing_array)
    x_samples_tf = tf_transformer.transform(x_samples)

    prediction = clf.predict(x_samples_tf)
    for desc, category in zip(testing_array, prediction):
        print('{} => {}'.format(desc, uniques[category]))
    mean_value = numpy.mean(prediction == y_test)
    print("Accuracy: {}".format(mean_value))
    # save the model, vectorizer and transformer to disk
    filename = 'finalized_model.sav'
    pickle.dump(clf, open(filename, 'wb'))
    filename = 'vectorizer.sav'
    pickle.dump(vectorizer, open(filename, 'wb'))
    filename = 'tfidftransformer.sav'
    pickle.dump(tf_transformer, open(filename, 'wb'))
    # Do report
    print(metrics.classification_report(y_test, prediction,
                                        target_names=['New feature', 'Improvement',
                                                      'Test', 'Bug']))
    # Uncomment when visualisations of the data are output of the
    # dataset preparation. Otherwise output model,
    # vectorized and tfidf tranformer as output of the dataset_preparation.
    import sys
    sys.exit()

    """
    Show dataset using matplotlib
    """
    nltk.download('stopwords')
    nltk.download('punkt')
    plt.style.use("seaborn-notebook")

    SMALL_SIZE = 12
    MEDIUM_SIZE = 15
    BIGGER_SIZE = 18

    plt.rc("font", size=SMALL_SIZE)
    plt.rc("axes", titlesize=BIGGER_SIZE)
    plt.rc("axes", labelsize=MEDIUM_SIZE)
    plt.rc("xtick", labelsize=SMALL_SIZE)
    plt.rc("ytick", labelsize=SMALL_SIZE)
    plt.rc("legend", fontsize=SMALL_SIZE)
    plt.rc("figure", titlesize=BIGGER_SIZE)

    r = matplotlib.patches.Rectangle(
        (0, 0), 1, 1, fill=False, edgecolor="none", visible=False
    )

    stop_words = set(stopwords.words("english"))
    stemmer = SnowballStemmer("english")
    # table = str.maketrans("", "", str.punctuation + "——")


    def remove_stop_words_and_tokenize(text: str) -> str:
        tokens = word_tokenize(text)
        tokens = [w.lower() for w in tokens]
        # stripped = [w.translate(table) for w in tokens]
        words = [word for word in tokens if word.isalpha()]
        words = [w for w in words if w not in stop_words]
        words = [stemmer.stem(w) for w in words]
        return " ".join(words)

    X_prep = []
    X_prep.append(
        [remove_stop_words_and_tokenize(x) for x in df['Description'].values]
    )

    tfidfs = []
    X_tfidf = []

    for X in X_prep:
        tfidf = TfidfVectorizer(max_features=20_000)
        X_tfidf.append(tfidf.fit_transform(X))
        tfidfs.append(tfidf)

    for X in X_tfidf:
        print(X.shape)

    embeddings = ["tfidf"]#, "average_fasttext"]#, "avg_glove", "distiluse",
                  #"roberta"]
    X_emb_umap = []
    All_umaps = []

    for embedding in embeddings:
        X_umap = []
        umaps = []

        if embedding == "tfidf":
            for X in X_tfidf:
                umap = UMAP(random_state=42, min_dist=0.1, metric="hellinger")
                X_umap.append(umap.fit_transform(X))
                umaps.append(umap)
        # else:
        #     for x_desc in zip(df['category_id'].values):#, y_datasets):
        #         umap = UMAP(random_state=42, min_dist=0.1, metric="cosine")
        #         X_umap.append(
        #             umap.fit_transform(
        #                 x_desc
        #             )
        #         )
        #         umaps.append(umap)

        All_umaps.append(umaps)
        X_emb_umap.append(X_umap)

    from itertools import chain
    for embedding, X_umap in zip(embeddings, X_emb_umap):
        # fig, axs = plt.subplots(2, 2, figsize=(20, 20))
        fig = plt.figure()
        plt.tight_layout()
        ax = fig.add_subplot(111)
        name = df['source']
        for X in X_umap:
            for color, label in zip(tab10.colors, numpy.unique(df['Issue Type'])):
                ax.scatter(*X[df['Issue Type'] == label].T, color=color,
                           alpha=0.6, label=label)
                plt.tight_layout()
            ax.set_title(f"{name} ({embedding})")
            # ax.set_xticks([])
            # ax.set_yticks([])
            ax.legend()
        # for X, ax in zip(X_umap, chain(*axs)):
        #     name = df['Issue Type']
        #     ax.set_title(f"{name} ({embedding})")
        #     for color, label in zip(tab10.colors, numpy.unique(df['source'])):
         #         ax.scatter(*X[df['source'] == label].T, color=color, alpha=0.6, label=label)
        #     ax.set_xticks([])
        #     ax.set_yticks([])
        #     ax.legend()
        plt.savefig(f"imgs/{embedding}-full.png", transparent=False)
        plt.show()