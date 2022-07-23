"""
A custom submission type to evaluate SQL queries
"""
from xblock.core import XBlock
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from .mixins.dates import EnforceDueDates
from .mixins.fragment import XBlockFragmentBuilderMixin
from .mixins.grading import Scorable, XBlockDataMixin
from .mixins.scenario import XBlockWorkbenchMixin


def _(text):
    """
    Mock translation helper
    """
    return text


@XBlock.needs('i18n')
class SqlGrader(
        XBlockDataMixin,
        EnforceDueDates,
        StudioEditableXBlockMixin,
        Scorable,
        XBlockFragmentBuilderMixin,
        XBlockWorkbenchMixin,
        XBlock,
):
    """
    A custom submission type to evaluate SQL queries
    """

    loader = ResourceLoader(__name__)
    public_dir = 'static'
    static_css = [
        'view.css',
        'codemirror/lib/codemirror.css',
        'codemirror/addon/hint/show-hint.css',
    ]
    static_js = [
        'view.js',
        'codemirror/lib/codemirror.js',
        'codemirror/mode/sql.js',
        'codemirror/addon/edit/matchbrackets.js',
        'codemirror/addon/hint/show-hint.js',
        'codemirror/addon/hint/sql-hint.js',
    ]
    static_js_init = 'SqlGrader'

    @XBlock.json_handler
    def submit_query(self, data, suffix=''):
        """
        Handle a user's query submission
        """
        # pylint: disable=unused-argument
        query = data.get('query') or ''
        query = str(query)
        query = query.strip()
        self.raw_response = query
        score, actual, expected, error, comparison = self._calculate_score()
        self.set_score(score)
        self._publish_grade(score)
        return {
            'comparison': comparison,
            'result': actual,
            'expected': expected,
            'verify': self.verify_query,
            'modification': self.modification_query,
            'error': error,
        }
