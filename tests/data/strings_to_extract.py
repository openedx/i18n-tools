"""
Test file that has some Python code with strings that need extracting.
"""
from django.utils.translation import ugettext as _


def view_fn(foo, bar):
    message_1 = _("Hello {user}!").format(user=foo)
    message_2 = _("Goodbye, thanks for using {platform_name} system!").format(platform_name=bar)
    message_3 = _("Bad %(count)d syntax %(name)s").format(17, 'Ducky')
    return (message_1, message_2, message_3)
