# Copyright (c) 2026 Mark Buckaway.
# SPDX-License-Identifier: LicenseRef-Proprietary
# All rights reserved.
#
# This file is proprietary and confidential. Unauthorized copying, distribution,
# or use of this file, via any medium, is strictly prohibited without the
# express written permission of Mark Buckaway.
"""Tests for the ``cyql version`` command."""

from typer.testing import CliRunner

from cyql import __version__
from cyql.cli.main import app

runner = CliRunner()


def test_version_command_outputs_installed_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__
