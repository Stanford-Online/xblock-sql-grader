#!/usr/bin/env python
"""
Test basic XBlock display function
"""
from unittest import TestCase
from unittest.mock import Mock

from opaque_keys.edx.locator import CourseLocator
from xblock.field_data import DictFieldData

from sql_grader.xblocks import SqlGrader


def make_an_xblock(**kwargs):
    """
    Helper method that creates a Free-text Response XBlock
    """
    course_id = CourseLocator('foo', 'bar', 'baz')
    runtime = Mock(
        course_id=course_id,
        service=Mock(
            # Is there a cleaner mock to the `i18n` service?
            return_value=Mock(_catalog={}),
        ),
    )
    scope_ids = Mock()
    field_data = DictFieldData(kwargs)
    xblock = SqlGrader(runtime, field_data, scope_ids)
    xblock.xmodule_runtime = runtime
    return xblock


class TestRender(TestCase):
    """
    Test the HTML rendering of the XBlock
    """

    def setUp(self):
        self.xblock = make_an_xblock()

    def test_render(self):
        """
        Ensure we can render a basic XBlock
        """
        student_view = self.xblock.student_view()
        html = student_view.content
        self.assertIsNotNone(html)
        self.assertNotEqual('', html)
        self.assertIn('sql_grader_block', html)
