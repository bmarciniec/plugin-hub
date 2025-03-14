"""Utility functions for the PluginHub package."""
import datetime
import locale


def date_to_str(date: datetime.date) -> str:
    """Convert a date to a string in the user's default locale.

    Args:
        date: Date to convert.

    Returns:
        str: Date as a string in the user's default locale.
    """
    current_locale = locale.getlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, '')
    date_as_str = date.strftime('%x')
    locale.setlocale(locale.LC_TIME, current_locale)
    return date_as_str
