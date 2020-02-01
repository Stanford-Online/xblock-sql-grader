"""
Mixin grading-related functionality
"""
from xblock.fields import Float
from xblock.fields import Integer
from xblock.fields import Scope
from xblock.scorable import ScorableXBlockMixin
from xblock.scorable import Score

from ..models import SqlProblem
from ..models import DATABASES


def _(text):
    """
    Mock translation for scraping
    """
    return text


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
        database = DATABASES[self.dataset]
        problem = SqlProblem(
            database,
            self.answer_query,
            self.verify_query,
            self.is_ordered,
        )
        response = self.raw_response
        actual, expected, error, comparison = problem.attempt(response)
        if comparison:
            raw_earned = 1.0
        score = Score(
            raw_earned=raw_earned,
            raw_possible=raw_possible,
        )
        return (score, actual, expected, error, comparison)
