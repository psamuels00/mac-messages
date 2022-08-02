from .config import *
from .db_access import count_messages
from .util import search_all

import os
import re


def message_count_header(search, page_size):
    num_messages = count_messages(search)
    matching = "" if search_all(search) else f" matching /{search}/"

    line = f"{num_messages} messages{matching}"
    if num_messages > page_size:
        line += f".  Showing only {page_size}"
    line += "."

    return [line, ""]


def text_content(rows, search, page_size):
    columns = int(os.environ.get("COLUMNS", default_text_columns))
    fixed_columns = 88  # num columns dedicated to all fields except the last, "text"
    text_columns = columns - fixed_columns
    dashes = "-" * text_columns

    content = message_count_header(search, page_size)

    content += [f"#       date/time            service_name  chat_id                 originator  tapback  text"]
    content += [f"------  -------------------  ------------  ----------------------  ----------  -------  {dashes}"]

    for row in rows:
        (row_num, date, service_name, chat_id, is_from_me, tapback, text, *extra) = row

        num = row_num
        if not search_all(search):
            match_offset, match_index = extra
            num = match_index if match_offset == 0 else ""

        who = icon_me if is_from_me else icon_you
        text = re.sub(r"\n", r"\\n", text)
        text = text[0:text_columns]

        content += [f"{num:6}  {date:19}  {service_name:12}  {chat_id:22}  {who:9}  {tapback:7}  {text}"]
        # note the width used for who is one less than the actual number of columns
        # that is needed since the value, a smiley, takes two columns

    content = "".join([f"{line}\n" for line in content])
    return content
