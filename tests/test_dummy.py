# -*- coding: utf-8 -*-
"""Tests of i18n/dummy.py"""

import ddt
from polib import POEntry

from i18n import dummy

from . import I18nToolTestCase,MOCK_APPLICATION_DIR


@ddt.ddt
class TestDummy(I18nToolTestCase):
    """
    Tests functionality of i18n/dummy.py
    """

    def setUp(self, root_dir=MOCK_APPLICATION_DIR, preserve_locale_paths=None, clean_paths=None):
        super(TestDummy, self).setUp()
        self.converter = dummy.Dummy()

    def assertUnicodeEquals(self, str1, str2):
        """Just like assertEquals, but doesn't put Unicode into the fail message.

        Either nose, or rake, or something, deals very badly with unusual
        Unicode characters in the assertions, so we use repr here to keep
        things safe.

        """
        self.assertEquals(
            str1, str2,
            "Mismatch: %r != %r" % (str1, str2),
        )

    @ddt.data(
        (u"sign in",
         u"sïgn ïn Ⱡ'σяєм ιρѕυм #"),

        (u"my name is Bond",
         u"mý nämé ïs Bönd Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт α#"),

        (u"hello my name is Bond, James Bond",
         u"héllö mý nämé ïs Bönd, Jämés Bönd Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢тє#"),

        (u"don't convert <a href='href'>tag ids</a>",
         u"dön't çönvért <a href='href'>täg ïds</a> Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє#"),

        (u"don't convert %(name)s tags on %(date)s",
         u"dön't çönvért %(name)s tägs ön %(date)s Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢#"),

        (u"don't convert %s tags on %s",
         u"dön't çönvért %s tägs ön %s Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢#"),
    )
    def test_dummy(self, data):
        """
        Tests with a dummy converter (adds spurious accents to strings).
        Assert that embedded HTML and Python tags are not converted.
        """
        source, expected = data
        result = self.converter.convert(source)
        self.assertUnicodeEquals(result, expected)

    def test_singular(self):
        entry = POEntry()
        entry.msgid = "A lovely day for a cup of tea."
        expected = u"À lövélý däý för ä çüp öf téä. Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢т#"
        self.converter.convert_msg(entry)
        self.assertUnicodeEquals(entry.msgstr, expected)

    def test_plural(self):
        entry = POEntry()
        entry.msgid = "A lovely day for a cup of tea."
        entry.msgid_plural = "A lovely day for some cups of tea."
        expected_s = u"À lövélý däý för ä çüp öf téä. Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢т#"
        expected_p = u"À lövélý däý för sömé çüps öf téä. Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢тєт#"
        self.converter.convert_msg(entry)
        result = entry.msgstr_plural
        self.assertUnicodeEquals(result['0'], expected_s)
        self.assertUnicodeEquals(result['1'], expected_p)

    @ddt.data(
        (u"sign in",
         u"سهلر هر"),

        (u"my name is Bond",
         u"وغ رشوث هس زخري"),

        (u"hello my name is Bond, James Bond",
         u"اثممخ وغ رشوث هس زخري, تشوثس زخري"),

        (u"don't convert <a href='href'>tag ids</a>",
         u"يخر'ف ذخردثقف <a href='href'>فشل هيس</a>"),

        (u"don't convert %(name)s tags on %(date)s",
         u"يخر'ف ذخردثقف %(name)s فشلس خر %(date)s"),

        (u"don't convert %s tags on %s",
         u"يخر'ف ذخردثقف %s فشلس خر %s"),
    )
    def test_dummy_arabic(self, data):
        """
        Tests with a dummy Arabic converter for RTL.
        Assert that embedded HTML and Python tags are not converted.
        """
        source, expected = data
        result = dummy.ArabicDummy().convert(source)
        self.assertUnicodeEquals(result, expected)
