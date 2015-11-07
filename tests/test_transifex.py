"""
This test tests that calls to Transifex work as expected.
"""
from contextlib import contextmanager
from mock import patch
from unittest import TestCase

from i18n import transifex


@contextmanager
def mockRawInput(mock_name):
    original_raw_input = __builtins__['raw_input']
    __builtins__['raw_input'] = lambda _: mock_name
    yield
    __builtins__['raw_input'] = original_raw_input


class TestTransifex(TestCase):
    """
    Tests functionality of i18n/transifex.py
    because Ned is making me write tests.
    """
    def setUp(self):
        self.patcher = patch('i18n.transifex.execute')
        self.addCleanup(self.patcher.stop)
        self.mock_execute = self.patcher.start()

    def test_push_command(self):
        # Call the push command
        transifex.push()
        self.assertTrue(self.mock_execute.called)
        self.assertEqual(
            'tx push -s',
            self.mock_execute.call_args[0][0]
        )

    def test_push_all_command(self):
        # Call the push_all command
        with mockRawInput('Y'):
            transifex.push_all()
        self.assertTrue(self.mock_execute.called)
        self.assertEqual(
            'tx push -s -t --force --skip --no-interactive',
            self.mock_execute.call_args[0][0]
        )

    def test_pull_command(self):
        # Call the pull command
        transifex.pull()
        # conf/locale/config.yaml specifies two non-source locales, 'fr' and 'zh_CN'
        self.assertEqual(2, self.mock_execute.call_count)

        call_args = [('tx pull --mode=reviewed -l fr',), ('tx pull --mode=reviewed -l zh_CN',)]
        self.assertEqual(
            call_args,
            [callarg[0] for callarg in self.mock_execute.call_args_list]
        )

    def test_clean_translated_locales(self):
        with patch('i18n.transifex.clean_locale') as patched:
            transifex.clean_translated_locales(langs=['fr', 'zh_CN'])
            self.assertEqual(2, patched.call_count)
            call_args = [('fr',), ('zh_CN',)]
            self.assertEqual(
                call_args,
                [callarg[0] for callarg in patched.call_args_list]
            )

    def test_clean_locale(self):
        with patch('i18n.transifex.clean_file') as patched:
            transifex.clean_locale('fr')
            self.assertEqual(3, patched.call_count)
            call_args = ['django-partial.po', 'djangojs-partial.po', 'mako.po']
            for callarg, expected in zip(patched.call_args_list, call_args):
                self.assertEqual(
                    callarg[0][0].name,
                    expected
                )
