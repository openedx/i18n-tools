"""
This test tests that calls to Transifex work as expected.
"""

import mock

from i18n import transifex

from . import I18nToolTestCase


class TestTransifex(I18nToolTestCase):
    """
    Tests functionality of i18n/transifex.py
    because Ned is making me write tests.
    """

    def setUp(self):
        super(TestTransifex, self).setUp()
        self._setup_i18n_test_config()
        self.patcher = mock.patch('i18n.transifex.execute')
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

    def test_push_command_with_resources(self):
        # Call the push command
        transifex.push("foo.1", "foo.2")

        call_args = [
            ('tx push -s -r foo.1',),
            ('tx push -s -r foo.2',),
        ]
        self.assertEqual(
            call_args,
            [callarg[0] for callarg in self.mock_execute.call_args_list]
        )

    def test_push_all_command(self):
        # Call the push_all command
        with mock.patch('i18n.transifex.input', return_value="Y"):
            transifex.push_all()
        self.assertTrue(self.mock_execute.called)
        self.assertEqual(
            'tx push -s -t --force --skip --no-interactive',
            self.mock_execute.call_args[0][0]
        )

    def test_pull_command(self):
        # Call the pull command
        transifex.pull(self.configuration)

        call_args = [
            ('tx pull -f --mode=reviewed -l en',),
            ('tx pull -f --mode=reviewed -l fr',),
            ('tx pull -f --mode=reviewed -l zh_CN',),
        ]
        self.assertEqual(
            call_args,
            [callarg[0] for callarg in self.mock_execute.call_args_list]
        )

    def test_pull_command_with_resources(self):
        # Call the pull command
        transifex.pull(self.configuration, "foo.1", "foo.2")

        # conf/locale/config.yaml specifies two non-source locales, 'fr' and 'zh_CN'
        call_args = [
            ('tx pull -f --mode=reviewed -l en -r foo.1',),
            ('tx pull -f --mode=reviewed -l en -r foo.2',),
            ('tx pull -f --mode=reviewed -l fr -r foo.1',),
            ('tx pull -f --mode=reviewed -l fr -r foo.2',),
            ('tx pull -f --mode=reviewed -l zh_CN -r foo.1',),
            ('tx pull -f --mode=reviewed -l zh_CN -r foo.2',),
        ]
        self.assertEqual(
            call_args,
            [callarg[0] for callarg in self.mock_execute.call_args_list]
        )

    def test_clean_translated_locales(self):
        with mock.patch('i18n.transifex.clean_locale') as patched:
            transifex.clean_translated_locales(self.configuration, langs=['fr', 'zh_CN'])
            self.assertEqual(2, patched.call_count)
            call_args = [
                (self.configuration, 'fr'),
                (self.configuration, 'zh_CN'),
            ]
            self.assertEqual(
                call_args,
                [callarg[0] for callarg in patched.call_args_list]
            )

    def test_clean_locale(self):
        with mock.patch('i18n.transifex.clean_file') as patched:
            transifex.clean_locale(self.configuration, 'fr')
            self.assertEqual(3, patched.call_count)
            call_args = ['django-partial.po', 'djangojs-partial.po', 'mako.po']
            for callarg, expected in zip(patched.call_args_list, call_args):
                self.assertEqual(
                    callarg[0][1].name,
                    expected
                )
