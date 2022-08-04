from .db_sql import (
    create_message_view_sql,
    drop_message_view_sql,
    messages_count_sql,
    messages_sql,
)

import os
import re
import sqlite3


def regexp(pattern, value):
    if value is None:
        return pattern == "^$"
    return re.search(pattern, value, re.IGNORECASE) is not None


def open_database():
    home = os.environ["HOME"]
    conn = sqlite3.connect("chat.db")
    conn.create_function("REGEXP", 2, regexp)
    return conn


def count_messages(search):
    db = open_database()
    cursor = db.cursor()
    cursor.execute(create_message_view_sql())
    cursor.execute(messages_count_sql(search))
    rows = cursor.fetchall()
    cursor.execute(drop_message_view_sql())

    return rows[0][0]


def select_messages(search, page, page_size, context_size):
    db = open_database()
    cursor = db.cursor()
    cursor.execute(create_message_view_sql())
    cursor.execute(messages_sql(search, page, page_size, context_size))
    rows = cursor.fetchall()
    cursor.execute(drop_message_view_sql())

    return rows
