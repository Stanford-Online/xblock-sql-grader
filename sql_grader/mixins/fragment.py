"""
Mixin fragment/html behavior into XBlocks

Note: We should resume test coverage for all lines in this file once
split into its own library.
"""
from xblock.core import XBlock
from web_fragments.fragment import Fragment


class XBlockFragmentBuilderMixin:
    """
    Create a default XBlock fragment builder
    """
    static_css = [
        'view.css',
    ]
    static_js = [
        'view.js',
    ]
    static_js_init = None
    template = 'view.html'

    def provide_context(self, context):  # pragma: no cover
        """
        Build a context dictionary to render the student view

        This should generally be overriden by child classes.
        """
        context = context or {}
        context = dict(context)
        return context

    @XBlock.supports('multi_device')
    def student_view(self, context=None):
        """
        Build the fragment for the default student view
        """
        template = self.template
        context = self.provide_context(context)
        static_css = self.static_css or []
        static_js = self.static_js or []
        js_init = self.static_js_init
        fragment = self.build_fragment(
            template=template,
            context=context,
            css_files=static_css,
            js_files=static_js,
            js_init=js_init,
        )
        return fragment

    # pylint: disable=too-many-arguments
    def build_fragment(
            self,
            template='',
            context=None,
            css_files=None,
            js_files=None,
            js_init=None,
    ):
        """
        Creates a fragment for display.
        """
        context = context or {}
        css_files = css_files or []
        js_files = js_files or []
        rendered_template = ''
        if template:  # pragma: no cover
            template = 'templates/' + template
            rendered_template = self.loader.render_django_template(
                template,
                context=context,
                i18n_service=self.runtime.service(self, 'i18n'),
            )
        fragment = Fragment(rendered_template)
        for item in css_files:
            if item.startswith('/'):
                url = item
            else:
                item = 'static/' + item
                url = self.runtime.local_resource_url(self, item)
            fragment.add_css_url(url)
        for item in js_files:
            item = 'static/' + item
            url = self.runtime.local_resource_url(self, item)
            fragment.add_javascript_url(url)
        if js_init:  # pragma: no cover
            fragment.initialize_js(js_init)
        return fragment
    # pylint: enable=too-many-arguments
