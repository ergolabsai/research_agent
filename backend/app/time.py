# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    APP_TIMEZONE = ZoneInfo("America/Los_Angeles")
except ZoneInfoNotFoundError:
    APP_TIMEZONE = timezone.utc


def now() -> datetime:
    return datetime.now(APP_TIMEZONE)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
