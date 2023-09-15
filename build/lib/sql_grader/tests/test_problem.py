#!/usr/bin/env python
"""
Test basic XBlock display function
"""
import os

from unittest import TestCase

from sql_grader.problem import SqlProblem


class TestGrading(TestCase):
    """
    Test grading of different types of problems
    """
    def setUp(self):
        current_folder = os.path.dirname(__file__)
        sql_file = "{0}/../datasets/rating.sql".format(current_folder)
        self.database = SqlProblem.create_database(sql_file)

    def test_select_returning_matching_results_in_wrong_order(self):
        """
        In a problem which is set up to be order-sensitive, test that a SELECT
        statement that returns the expected set of results but in the wrong
        order won't be accepted as matching the answer.
        """
        answer_query = "SELECT * FROM Movie order by mID desc;"
        query = "SELECT * FROM Movie order by mID asc;"
        submission_result, answer_result, error, comparison = SqlProblem(
            answer_query=answer_query,
            database=self.database,
            verify_query=None,
            is_ordered=True
        ).attempt(query)
        self.assertEqual(error, None)
        self.assertEqual(comparison, False)
        self.assertEqual(submission_result, sorted(answer_result))

    def test_select_returning_matching_results_in_unordered_problem(self):
        """
        In a problem which isn't order-sensitive, test that a SELECT
        statement that returns the expected set of results is accepted.
        """
        answer_query = "SELECT * FROM Movie order by mID desc;"
        query = "SELECT * FROM Movie order by mID asc;"
        submission_result, answer_result, error, comparison = SqlProblem(
            answer_query=answer_query,
            database=self.database,
            verify_query=None,
            is_ordered=False
        ).attempt(query)
        self.assertEqual(error, None)
        self.assertEqual(comparison, True)
        self.assertEqual(submission_result, sorted(answer_result))
        self.assertNotEqual(submission_result, answer_result)

    def test_select_with_different_rows_returned(self):
        """
        Test that a SELECT that returns different rows to the expected rows
        isn't considered as matching the answer.
        """
        answer_query = "SELECT * FROM Movie order by mID desc;"
        query = "select * from Movie where mID=101"
        _, _, error, comparison = SqlProblem(
            answer_query=answer_query,
            database=self.database,
            verify_query=None,
            is_ordered=False
        ).attempt(query)
        self.assertEqual(error, None)
        self.assertEqual(comparison, False)

    def test_select_with_different_columns_returned(self):
        """
        Test that a SELECT that returns different columns that don't match the
        columns in the answer isn't considered as matching the answer.
        """
        answer_query = "SELECT * FROM Movie order by mID desc;"
        query = "select mID from Movie where mID"
        _, _, error, comparison = SqlProblem(
            answer_query=answer_query,
            database=self.database,
            verify_query=None,
            is_ordered=False
        ).attempt(query)
        self.assertEqual(error, None)
        self.assertEqual(comparison, False)

    def test_update_statements(self):
        """
        Test statements which modify the table
        """
        verify_query = "SELECT * FROM Movie where mID = 1"
        answer_query = "insert into Movie values(1, 'Movie', 2000, 'Director')"
        query = """
        update Movie
        set mID=1, title='Movie', year=2000, director='Director'
        where mID=101;
        """

        submission_result, answer_result, error, comparison = SqlProblem(
            answer_query=answer_query,
            database=self.database,
            verify_query=verify_query,
            is_ordered=False
        ).attempt(query)

        self.assertEqual(error, None)
        self.assertEqual(comparison, True)
        self.assertEqual(submission_result, answer_result)
        self.assertEqual(len(submission_result), 1)

    def test_multiple_statements(self):
        """
        Test queries with multiple statements in them
        """
        verify_query = "select * from Movie where mID < 10"
        answer_query = """
        insert into Movie values(1, 'Movie', 2000, 'Director');
        insert into Movie values(2, 'Movie 2', 2000, 'Director 2');
        """
        query = """
        update Movie
        set mID=1, title='Movie', year=2000, director='Director'
        where mID=101;
        insert into Movie values(2, 'Movie 2', 2000, 'Director 2');
        """

        submission_result, answer_result, error, comparison = SqlProblem(
            answer_query=answer_query,
            database=self.database,
            verify_query=verify_query,
            is_ordered=False
        ).attempt(query)

        self.assertEqual(error, None)
        self.assertEqual(comparison, True)
        self.assertEqual(submission_result, answer_result)
        self.assertEqual(len(submission_result), 2)

        verify_query = """
        insert into Movie values(3, 'Movie', 2000, 'Director 3');
        SELECT * FROM Movie where mID < 10;
        """
        submission_result, answer_result, error, comparison = SqlProblem(
            answer_query=answer_query,
            database=self.database,
            verify_query=verify_query,
            is_ordered=False
        ).attempt(query)

        self.assertNotEqual(error, None)

    def test_pre_verification(self):
        """
        Test that modification_query is executed before checking outputs
        """
        answer_query = """
        create trigger change1
        after insert on Movie
        for each row
        when (new.year > 1980 and new.year < 1990)
          begin update Movie
            set title="80s movie" where mID=new.mID; end;

        create trigger change2
        after insert on Movie
        for each row
        when (new.year is NULL)
          begin update Movie
            set director=NULL where mID=new.mID; end;
        """
        query = answer_query
        modification_query = """
        insert into Movie values (1, "E.T.", 1982, "Steven Spielberg");
        insert into Movie values (2, null, 1992, "David Fincher");
        """
        verify_query = """
        select * from Movie
        where title like '80s %' or title IS NULL
        """

        submission_result, answer_result, error, comparison = SqlProblem(
            answer_query=answer_query,
            database=self.database,
            verify_query=verify_query,
            modification_query=modification_query,
            is_ordered=False
        ).attempt(query)
        self.assertEqual(error, None)
        self.assertEqual(comparison, True)
        self.assertEqual(submission_result, answer_result)
        self.assertEqual(submission_result, [
            (1, '80s movie', 1982, 'Steven Spielberg'),
            (2, None, 1992, 'David Fincher')
        ])

    def test_error_with_invalid_answer_query(self):
        """
        Verify that a syntax error is displayed when answer_query
        contains errors.
        """
        _, _, error, _ = SqlProblem(
            answer_query="Not a query;",
            database=self.database,
            verify_query=None,
            is_ordered=True
        ).attempt("SELECT * FROM Movie;")
        self.assertIn("Problem setup incorrectly", error)
        self.assertIn("syntax error", error)

    def test_error_with_invalid_verify_query(self):
        """
        Verify that a syntax error is displayed when verify_query
        contains errors.
        """
        _, _, error, _ = SqlProblem(
            answer_query="",
            database=self.database,
            verify_query="Not a query;",
            is_ordered=True
        ).attempt("Not a SQL Query;")
        self.assertIn("Problem setup incorrectly", error)
        self.assertIn("verify_query", error)
        self.assertIn("syntax error", error)

    def test_error_with_invalid_modification_query(self):
        """
        Verify that a syntax error is displayed when modification_query
        contains errors.
        """
        _, _, error, _ = SqlProblem(
            answer_query="",
            database=self.database,
            verify_query="SELECT;",
            modification_query="Not a query;",
            is_ordered=True
        ).attempt("Not a SQL Query;")
        self.assertIn("Problem setup incorrectly", error)
        self.assertIn("modification_query", error)
        self.assertIn("syntax error", error)

    def test_error_with_invalid_submitted_query(self):
        """
        Verify that a syntax error is displayed when the submitted answer
        contains errors.
        """
        _, _, error, _ = SqlProblem(
            answer_query="SELECT * FROM Movie;",
            database=self.database,
            verify_query=None,
            is_ordered=True
        ).attempt("Not a SQL Query;")
        self.assertNotIn("Problem setup incorrectly", error)
        self.assertIn("syntax error", error)

    def test_error_with_valid_verify_query(self):
        """
        Verify that errors are displayed when the verification query is
        syntactically valid but errors out due to different error.
        """
        _, _, error, _ = SqlProblem(
            answer_query="",
            database=self.database,
            verify_query="select * from Movie",
            is_ordered=True
        ).attempt("alter table Movie rename to Movie2")
        self.assertNotIn("Problem setup incorrectly", error)
        self.assertIn("verify_query", error)
        self.assertIn("no such table", error)
