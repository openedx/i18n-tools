"""
Tests for integration between different parts of the i18n-tools packages
"""
import os
from datetime import datetime, timedelta
from functools import wraps
import itertools

import ddt
import sys
import io
from i18n import validate, config
from path import Path

from . import I18nToolTestCase, MOCK_DJANGO_APP_DIR

from . import test_extract


@ddt.ddt
class TestIntegration(test_extract.ExtractInitTestMixin):
    """
    Tests for integration between different parts of the i18n-tools packages
    """
    def verify_via_validate_command(self, check_all):
        """
        Helper to verify that extract and validate work together
        """
        return validate.main(
            verbosity=0,
            config=self.configuration._filename,
            root_dir=MOCK_DJANGO_APP_DIR,
            check_all=check_all,
        )

    @test_extract.perform_extract_with_options()
    def test_extract_then_validate(self):
        """
        Test that extract and validate work together
        """
        for check_all in [True, False]:
            # Extract is called by the `@test_extract.perform_extract_with_options()` helper.
            result = self.verify_via_validate_command(check_all)

            assert result == 0, (
                'Validation after extract failed, see (Captured log call) for details\n'
                f'extract options: merge_po_files={self.ddt_flag_merge_po_files}, no_segment={self.ddt_flag_no_segment}\n'
                f'validate options: check_all={check_all}'
            )
