"""
Mixin grading-related functionality
"""
import logging
import os.path

# pylint: disable=wrong-import-order
# We shouldn't need this pylint pragma, but we do...
# Otherwise, it complains about the code jail import,
# despite it also being a third-party package.
from codejail.safe_exec import safe_exec
from codejail.safe_exec import SafeExecException
from django.utils.translation import ugettext_lazy as _
from xblock.fields import Boolean
from xblock.fields import Float
from xblock.fields import Integer
from xblock.fields import Scope
from xblock.fields import String
from xblock.scorable import ScorableXBlockMixin
from xblock.scorable import Score
# pylint: enable=wrong-import-order

from ..problem import all_datasets


log = logging.getLogger('sql_grader')


# pylint: disable=too-many-arguments
def attempt_safe(dataset, answer_query, verify_query, modification_query,
                 is_ordered, query):
    """
    Attempt a SqlProblem, using codejail to sandbox the execution.
    """
    results = {
        'answer_query': answer_query,
        'dataset': dataset,
        'verify_query': verify_query,
        'modification_query': modification_query,
        'is_ordered': is_ordered,
        'query': query
    }
    code = """
from sql_grader.problem import SqlProblem
submission_result, answer_result, error, comparison = SqlProblem(
    answer_query=answer_query,
    dataset=dataset,
    verify_query=verify_query,
    modification_query=modification_query,
    is_ordered=is_ordered
).attempt(query)

"""
    # example from edx-platform's use of codejail:
    # https://github.com/openedx/edx-platform/blob/master/common/lib/capa/capa/capa_problem.py#L887
    # we have to include the path to the entire sql_grader package.
    python_path = [os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            '../..'
        )
    )]

    try:
        safe_exec(code, results, python_path=python_path, slug='sql_grader')
    except SafeExecException:
        log.exception(query)
        # how should resource limits be communicated to the user?
        results = {
            'submission_result': None,
            'answer_result': None,
            'error': _("We could not execute your query; please try again."),
            'comparison': None,
        }
    return (
        results['submission_result'],
        results['answer_result'],
        results['error'],
        results['comparison'],
    )


class Scorable(ScorableXBlockMixin):
    """
    Implement basic scoring functionality
    """
    # pylint: disable=no-member
    weight = Integer(
        display_name=_('Weight'),
        help=_(
            'This assigns an integer value representing '
            'the weight of this problem'
        ),
        default=0,
        values={'min': 1},
        scope=Scope.settings,
    )
    score = Float(
        default=0.0,
        scope=Scope.user_state,
    )

    def max_score(self):
        """
        Return the maximum possible score
        """
        return self.weight

    def get_score(self):
        """
        Get the problem score
        """
        score = None
        if self.has_submitted_answer():
            score = self.score
        return score

    def set_score(self, score):
        """
        Update the problem score
        """
        self.score = score.raw_earned
        return self

    def has_submitted_answer(self):
        """
        Check if an answer has been submitted for this problem
        """
        has_submitted = False
        if self.fields['score'].is_set_on(self):
            has_submitted = True
        return has_submitted

    def calculate_score(self):
        """
        Calculate user score, based on current answer
        """
        score, _, _, _, _ = self._calculate_score()
        return score

    def _calculate_score(self):
        """
        Calculate user score and provide relevant context
        """
        raw_possible = 1.0
        raw_earned = 0.0
        actual, expected, error, comparison = attempt_safe(
            self.dataset,
            self.answer_query,
            self.verify_query,
            self.modification_query,
            self.is_ordered,
            self.raw_response
        )
        if comparison:
            raw_earned = 1.0
        score = Score(
            raw_earned=raw_earned,
            raw_possible=raw_possible,
        )
        return (score, actual, expected, error, comparison)


class XBlockDataMixin:
    """
    Mixin XBlock field data
    """

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
        values=list(all_datasets()),
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
            '. Only enter a single SELECT query here, which is used for '
            'matching the answer'
        ),
        default='',
        scope=Scope.content,
        multiline_editor=True,
    )
    modification_query = String(
        display_name=_('Modification query statements'),
        help=_(
            'Optional SQL statements, to be executed after the '
            'user-submitted query, but before the verify_query.'
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
        'modification_query',
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
            'verify_query': self.verify_query,
            'modification_query': self.modification_query,
        })
        return context
