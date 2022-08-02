#!/usr/bin/env python

from messages.config import *
from messages.db_access import select_messages
from messages.text_out import text_content

import sys


def program_arg(index, value_type, default_value):
    if len(sys.argv) > index:
        return value_type(sys.argv[index])
    return default_value


def text_query():
    search = program_arg(1, str, None)
    page = program_arg(2, int, 1)
    page_size = program_arg(3, int, default_page_size)
    context_size = program_arg(4, int, default_context_size)

    rows = select_messages(search, page, page_size, context_size)
    print(text_content(rows, search, page_size))


if __name__ == '__main__':
    text_query()
