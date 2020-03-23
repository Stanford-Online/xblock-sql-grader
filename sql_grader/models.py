"""
Handle data modeling for the XBlock
"""
import os
import sqlite3

from django.utils.translation import ugettext_lazy as _
import pkg_resources

from xblock.fields import Boolean
from xblock.fields import Scope
from xblock.fields import String


class SqlProblem:
    """
    Handle modeling and processing of SQL problems aside from XBlock logic
    """

    dataset = None
    answer_query = None
    verify_query = None
    answer_result = None
    is_ordered = True

    def __init__(
            self,
            database,
            answer_query,
            verify_query=None,
            is_ordered=True,
    ):
        """
        Initialize variables
        """
        self.database = database
        self.is_ordered = is_ordered
        self.answer_query = answer_query
        self.verify_query = verify_query
        self.answer_result, _ = SqlProblem.run_query(
            database,
            answer_query,
            verify_query,
        )

    def attempt(self, query):
        """
        Attempt to answer the problem with the provided query
        """
        submission_result, error = SqlProblem.run_query(
            self.database,
            query,
            self.verify_query,
        )
        comparison = SqlProblem.compare_rows(
            self.answer_result,
            submission_result,
            is_ordered=self.is_ordered,
        )
        return (submission_result, self.answer_result, error, comparison)

    @classmethod
    def create_database(cls, path_sql):
        """
        Create a new in-memory database, initialized via SQL file

        This only needs run once, at startup.
        """
        with open(path_sql, 'r') as sql:
            query = sql.read()
        connection = cls.create_database_from_sql(query)
        return connection

    @classmethod
    def create_database_from_sql(cls, query):
        """
        Create a new in-memory database, initialized via SQL query
        """
        connection = sqlite3.connect(':memory:', check_same_thread=False)
        with connection:
            connection.executescript(query)
        return connection

    @staticmethod
    def clone_database(source):
        """
        Copy the contents of a source database into a new in-memory database

        This should be run for each request.
        """
        destination = sqlite3.connect(':memory:', check_same_thread=False)
        query = ''.join(line for line in source.iterdump())
        destination.executescript(query)
        return destination

    @classmethod
    def run_query(cls, source, query, verify_query=None):
        """
        Execute the provided SQL query against a copy of the database
        """
        def run(database, query):
            result = []
            message = None
            with database as connection:
                try:
                    for row in connection.execute(query):
                        result.append(row)
                except Exception as error:  # pylint: disable=broad-except
                    result = None
                    message = str(error)
            return result, message
        database = cls.clone_database(source)
        result, error = run(database, query)
        if verify_query:
            result, _ = run(database, verify_query)
        return result, error

    @staticmethod
    def compare_rows(expected, actual, is_ordered=True):
        """
        Compare the results of two queries
        """
        expected = expected or []
        actual = actual or []
        if len(expected) != len(actual):
            return False
        if not is_ordered:
            expected = sorted(expected)
            actual = sorted(actual)
        comparison = all(
            row_expected == row_actual
            for row_expected, row_actual in zip(expected, actual)
        )
        return comparison


def all_datasets():
    """
    Lookup the names of all avaiable datasets (.sql files)
    """
    dataset_directory = pkg_resources.resource_filename(
        'sql_grader',
        'datasets'
    )
    for _, _, files in os.walk(dataset_directory):
        for fname in files:
            if fname.endswith('.sql'):
                fname = fname[:-4]
                yield fname


def resource_string(path):
    """
    Handy helper for getting resources from our kit
    """
    data = pkg_resources.resource_string(__name__, path)
    return data.decode('utf8')


def create_database(database_name):
    """
    Load a new database from a dataset on disk
    """
    pathname = 'datasets/' + database_name + '.sql'
    contents = resource_string(pathname)
    database = SqlProblem.create_database_from_sql(contents)
    return database


# Memoize the seed databases
# to avoid continually loading from disk
DATABASES = {
    key: create_database(key)
    for key in all_datasets()
}


class XBlockDataMixin:
    """
    Mixin XBlock field data
    """
    # pylint: disable=too-few-public-methods

    display_name = String(
        display_name=_('Display Name'),
        help=_('The display name for this component.'),
        default=_('SQL Problem'),
        scope=Scope.content,
    )
    dataset = String(
        display_name=_('Dataset'),
        help=_('Which initial dataset/database to be used for queries'),
        default='rating',
        scope=Scope.content,
        values=DATABASES.keys(),
    )
    answer_query = String(
        display_name=_('Answer Query'),
        help=_('A correct response SQL query'),
        default='',
        scope=Scope.content,
        multiline_editor=True,
    )
    verify_query = String(
        display_name=_('Verify Query'),
        help=_(
            'A secondary verification SQL query, to be used if the '
            'answer_query modifies the database (UPDATE, INSERT, DELETE, etc.)'
        ),
        default='',
        scope=Scope.content,
        multiline_editor=True,
    )
    is_ordered = Boolean(
        display_name=_('Is Ordered?'),
        help=_('Should results be in order?'),
        default=False,
        scope=Scope.content,
    )
    editable_fields = [
        'answer_query',
        'dataset',
        'display_name',
        'verify_query',
        'is_ordered',
        'prompt',
        'weight',
    ]
    prompt = String(
        display_name=_('Prompt'),
        help=_('Explanatory text to accompany the problem'),
        default='',
        scope=Scope.content,
    )
    raw_response = String(
        display_name=_('Submission Query'),
        help=_('A Submission Query'),
        default='',
        scope=Scope.user_state,
    )

    def provide_context(self, context):  # pragma: no cover
        """
        Build a context dictionary to render the student view
        """
        context = context or {}
        context = dict(context)
        error_class = ''
        if not bool(self.score) and bool(self.raw_response):
            error_class = 'error'
        context.update({
            'display_name': self.display_name,
            'prompt': self.prompt,
            'answer': self.raw_response,
            'score': self.score,
            'score_weighted': int(self.score * self.weight),
            'max_score': int(self.max_score()),
            'error_class': error_class,
            'raw_response': self.raw_response,
        })
        return context
