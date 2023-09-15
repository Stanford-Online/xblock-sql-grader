"""
Handle data modeling for the XBlock
"""
import os
import sqlite3

import pkg_resources


class SqlProblem:
    """
    Handle modeling and processing of SQL problems aside from XBlock logic
    """

    dataset = None
    answer_query = None
    verify_query = None
    modification_query = None
    answer_result = None
    answer_error = None
    is_ordered = True

    # pylint: disable=too-many-arguments
    def __init__(
            self,
            database=None,
            answer_query=None,
            dataset=None,
            verify_query=None,
            modification_query=None,
            is_ordered=True,
    ):
        """
        Initialize variables
        """
        self.database = database
        if dataset:
            self.database = create_database(dataset)
        self.is_ordered = is_ordered
        self.answer_query = answer_query
        self.verify_query = verify_query
        self.modification_query = modification_query
        self.answer_result, self.answer_error = SqlProblem.run_query(
            self.database,
            answer_query,
            verify_query,
            modification_query,
        )

    def attempt(self, query):
        """
        Attempt to answer the problem with the provided query
        """
        if self.answer_error:
            return (
                None,
                None,
                'Problem setup incorrectly: {}'.format(self.answer_error),
                False
            )
        submission_result, error = SqlProblem.run_query(
            self.database,
            query,
            self.verify_query,
            self.modification_query,
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
        with open(path_sql) as sql:
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
    def run_query(cls, source, query, verify_query=None,
                  modification_query=None):
        """
        Execute the provided SQL queries against a copy of the database.
        """
        def run(database, query, is_single_query):
            result = []
            message = None
            with database as connection:
                try:
                    if is_single_query:
                        executor_func = connection.execute
                    else:
                        executor_func = connection.executescript
                    rows = executor_func(query)
                    # connection.executescript doesn't return anything, so the
                    # following loop would be a no-op in such cases.
                    for row in rows:
                        result.append(row)
                except Exception as error:  # pylint: disable=broad-except
                    result = None
                    message = str(error)
            return result, message

        database = cls.clone_database(source)

        # SELECT statements must be run as a single query to be able to
        # collect the results. When there's no verify_query in the problem,
        # we assume the SELECT statement must be in `query` and therefore
        # `query` must be run as a single query.
        is_single_query = not verify_query
        result, error = run(database, query, is_single_query=is_single_query)
        if error:
            return None, error

        if verify_query:
            if modification_query:
                _, error = run(database, modification_query,
                               is_single_query=False)
                if error:
                    return None, 'modification_query: {}'.format(error)

            result, error = run(database, verify_query,
                                is_single_query=True)
            if error:
                return None, 'verify_query: {}'.format(error)

        return result, None

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
            expected = sorted(expected, key=str)
            actual = sorted(actual, key=str)
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
