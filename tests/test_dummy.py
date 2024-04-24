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

    def setUp(self):
        super().setUp()
        self.converter = dummy.Dummy()

    def assertUnicodeEquals(self, str1, str2):
        """Just like assertEqual, but doesn't put Unicode into the fail message.

        Either nose, or rake, or something, deals very badly with unusual
        Unicode characters in the assertions, so we use repr here to keep
        things safe.

        """
        self.assertEqual(
            str1, str2,
            "Mismatch: %r != %r" % (str1, str2),
        )

    @ddt.data(
        ("sign in",
         "sïgn ïn Ⱡ'σяєм ιρѕυм #"),

        ("my name is Bond",
         "mý nämé ïs Bönd Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт α#"),

        ("hello my name is Bond, James Bond",
         "héllö mý nämé ïs Bönd, Jämés Bönd Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢тє#"),

        ("don't convert <a href='href'>tag ids</a>",
         "dön't çönvért <a href='href'>täg ïds</a> Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє#"),

        ("don't convert %(name)s tags on %(date)s",
         "dön't çönvért %(name)s tägs ön %(date)s Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢#"),

        ("don't convert %s tags on %s",
         "dön't çönvért %s tägs ön %s Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢#"),
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
        expected = "À lövélý däý för ä çüp öf téä. Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢т#"
        self.converter.convert_msg(entry)
        self.assertUnicodeEquals(entry.msgstr, expected)

    def test_plural(self):
        entry = POEntry()
        entry.msgid = "A lovely day for a cup of tea."
        entry.msgid_plural = "A lovely day for some cups of tea."
        expected_s = "À lövélý däý för ä çüp öf téä. Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢т#"
        expected_p = "À lövélý däý för sömé çüps öf téä. Ⱡ'σяєм ιρѕυм ∂σłσя ѕιт αмєт, ¢σηѕє¢тєт#"
        self.converter.convert_msg(entry)
        result = entry.msgstr_plural
        self.assertUnicodeEquals(result['0'], expected_s)
        self.assertUnicodeEquals(result['1'], expected_p)

    @ddt.data(
        ("sign in",
         "سهلر هر"),

        ("my name is Bond",
         "وغ رشوث هس زخري"),

        ("hello my name is Bond, James Bond",
         "اثممخ وغ رشوث هس زخري, تشوثس زخري"),

        ("don't convert <a href='href'>tag ids</a>",
         "يخر'ف ذخردثقف <a href='href'>فشل هيس</a>"),

        ("don't convert %(name)s tags on %(date)s",
         "يخر'ف ذخردثقف %(name)s فشلس خر %(date)s"),

        ("don't convert %s tags on %s",
         "يخر'ف ذخردثقف %s فشلس خر %s"),
    )
    def test_dummy_arabic(self, data):
        """
        Tests with a dummy Arabic converter for RTL.
        Assert that embedded HTML and Python tags are not converted.
        """
        source, expected = data
        result = dummy.ArabicDummy().convert(source)
        self.assertUnicodeEquals(result, expected)
