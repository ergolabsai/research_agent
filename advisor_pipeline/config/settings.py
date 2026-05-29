# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Re-export shim — the canonical settings module is `composition.settings`.

Existing call sites inside `advisor_pipeline` keep importing from here for the
duration of the migration; this file is removed in Step 5.
"""

from composition.settings import Settings, settings  # noqa: F401
