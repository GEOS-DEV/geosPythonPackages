# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware


def iterate_nested_dict( iterable, returned="key" ):
    """Returns an iterator that returns all keys or values
    of a (nested) iterable.

    Arguments:
        - iterable: <list> or <dictionary>
        - returned: <string> "key" or "value"

    Returns:
        - <iterator>
    """

    if isinstance( iterable, dict ):
        for key, value in iterable.items():
            if key == "id":
                if not ( isinstance( value, dict ) or isinstance( value, list ) ):
                    yield value
            # else:
            #     raise ValueError("'returned' keyword only accepts 'key' or 'value'.")
            for ret in iterate_nested_dict( value, returned=returned ):
                yield ret
    elif isinstance( iterable, list ):
        for el in iterable:
            for ret in iterate_nested_dict( el, returned=returned ):
                yield ret
