#!/usr/bin/env python

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

import os
import re
import sqlite3
import sys
import urllib.parse


# /////////////////////////////////////////////////////////////// configuration


default_text_columns = 100  # in case COLUMNS environment var not set
enable_diagnostics = False
icon_me = "🤓"
icon_you = "🐵"
num_context_messages = 3
page_size = 10


# /////////////////////////////////////////////////////////////// constants


link_stub = "~~~<<<:::@@@:::>>>~~~"
# any string not likely to be searched for, and not containing regular expression special chars

search_all_identifier = "-"
# will appear in the URL, also should be something not likely to be searched for


# /////////////////////////////////////////////////////////////// global vars


app = FastAPI(default_response_class=HTMLResponse)


# /////////////////////////////////////////////////////////////// misc


def search_all(search):
    return search is None or search == search_all_identifier


# /////////////////////////////////////////////////////////////// HTTP endpoints


@app.get("/")
async def hello():
    return menu()


@app.get("/message/count")
async def message_count():
    return str(count_messages())


@app.get("/message")
async def message():
    return select_messages('html')


@app.get("/message/{search}")
async def message_search(search):
    return select_messages('html', search)


@app.get("/message/{search}/{page}")
async def message_search_page(search, page :int):
    return select_messages('html', search, page)


# /////////////////////////////////////////////////////////////// HTML menu


def menu():
    return f"""
        <html>
        {head_with_style()}
        <body>
            Hello, chat world!<br/>
            <br/>
            Try an endpoint:
            <ul>
                <li><a href="/message/count">count</a> - total number of messages</li>
                <li>
                    <a href="/message">all</a> - all messages
                    -- jump to <a href="/message/-/2">page 2</a>,
                    <a href="/message/-/3">page 3</a>, ...
                </li>
                <li>
                    <a href="/message/dog">dog</a> - messages containing "dog"
                    -- jump to <a href="/message/dog/2">page 2</a>,
                    <a href="/message/dog/3">page 3</a>, ...
                </li>
                <li><a href="/message/dog%5Cw%2B">dog\w+</a> - messages matching /dog\w+/</li>
                <li><a href="/message/%5Cw%2Adog%5Cw%2A">\w*dog\w*</a> - messages matching /\w*dog\w*/</li>
                <li><a href="/message/aristotle">aristotle</a> - messages containing "aristotle"</li>
                <li><a href="/message/socrates">socrates</a> - messages containing "socrates"</li>
                <li><a href="/message/godzilla">godzilla</a> - messages containing "godzilla"</li>
            </ul>
            <hr/>
            <div>
                See <a href="https://www.urlencoder.io/">urlencoder.io</a> to encode search
                patterns in the url with special regular expression characters.  For example,
                this pattern:
                <pre>    dog\w+</pre>
                needs to be encoded as:
                <pre>    dog%5Cw%2B</pre>
            </div>
        </body>
    </html>
    """


# /////////////////////////////////////////////////////////////// HTML results


def head_with_style():
    return """
    <head>
    <style>
        body {
             font-family: sans-serif;
        }
        div {
            margin-bottom: 1em;
        }
        hr {
            margin: 2em 0em;
        }
        button {
            background-color: #9CC;
            padding: 7px 15px;
            border: none;
            border-radius: 5px;
        }
        button:hover {
            background-color: #699;
            color: white;
        }
        span.page-hint {
            color: #BBB;
            margin-left: 1em;
        }
        table { 
            border-collapse: collapse;
        }
        tr.context {
            color: #AAA;
        }
        th {
            border: 1px solid black;
            padding: 5px 5px;
        }
        td {
            border: 1px solid black;
            padding: 3px 5px;
        }
        th,
        td:first-child {
            background-color: #DDD;
        }
        td:last-child {
            word-break: break-all;
        }
        td.atomic {
            white-space: nowrap;
        }
        td.mine {
            padding-left: 10em;
        }
        td.yours {
        }
        td span.match {
            color: #3C3;
            font-weight: bold;
        }
    </style>
    </head>
    """

def message_count_section(search):
    num_messages = count_messages(search)

    content = ["<div>"]

    matching = "" if search_all(search) else f" matching /{search}/"
    content += [f"{num_messages} messages{matching}."]

    if num_messages > page_size:
        content += [f'<span class="page-hint">Showing {page_size} at a time.</span>']

    content += ["</div>"]

    return content


def menu_option(uri, label):
    return f'''
        <button onclick="window.location.href='{uri}';">
            {label}
        </button>
    '''


def navigation_menu(search, page):
    if page is None:
        return ""

    num_messages = count_messages(search)
    max_page = int(num_messages / page_size) + 1
    search = search_all_identifier if search_all(search) else search
    search = urllib.parse.quote_plus(search)

    return "".join([
        "<div>",
            menu_option("/", "Home"),
            menu_option(f"/message/{search}/1", "&lt;&lt;"),
            menu_option(f"/message/{search}/{page-1}", "&lt;"),
            menu_option(f"/message/{search}/{page+1}", "&gt;"),
            menu_option(f"/message/{search}/{max_page}", "&gt;&gt;"),
        "</div>"
    ])


def format_message(text, search):
    # The formatting is complicated by the possibility that the search pattern
    # is found in a link, which we do not want to disturb.
    #
    # Our solution is to
    #   1.  replace all the links with stubs, saving the links in an array
    #   2.  format matches on the search pattern
    #   3.  replace the stubs with links based on the saved links array

    saved_links = []

    def swap_link_with_stub(matchobj):
        url = matchobj.group(1)
        label = matchobj.group(2)
        saved_links.append((url, label))
        return link_stub

    def swap_stub_with_link(matchobj):
        url, label = saved_links[0]
        del saved_links[0]
        return rf'<a href="{url}" target="_blank">{label}</a>'

    text = re.sub(r"(https?://([^/]+)[^\s\"']*)", swap_link_with_stub, text)

    if not search_all(search):
        text = re.sub(f"({search})", r'<span class="match">\1</span>', text, 0, re.IGNORECASE)

    text = re.sub(link_stub, swap_stub_with_link, text)

    return text


def html_content(rows, search, page):
    content = []

    content += ["<html>"]
    content += [head_with_style()]
    content += ["<body>"]
    content += message_count_section(search)
    content += navigation_menu(search, page)
    content += ['<table>']

    content += ["<tr>"]
    labels = ("#", "date/time", "service", "chat id", "originator", "tapback", "text")
    if enable_diagnostics:
        labels = ("row#", "match offset", *labels)
    for label in labels:
        content += [f'<th>{label}</th>']
    content += ["</tr>"]

    for row in rows:
        (row_num, date, service_name, chat_id, is_from_me, tapback, text, *extra) = row

        num = row_num
        if not search_all(search):
            match_offset, match_index = extra
            num = match_index if match_offset == 0 else ""
        else:
            match_offset = "?"

        text = format_message(text, search)
        if is_from_me:
            whose_text = "mine"
            who = icon_me
        else:
            whose_text = "yours"
            who = icon_you

        row_class = "" if search_all(search) or match_offset == 0 else 'class="context"'
        content += [f"<tr {row_class}>"]

        if enable_diagnostics:
            content += [f"<td>{row_num}</td>"]
            content += [f"<td>{match_offset}</td>"]
        content += [f"<td>{num}</td>"]
        content += [f'<td class="atomic">{date}</td>']
        content += [f"<td>{service_name}</td>"]
        content += [f"<td>{chat_id}</td>"]
        content += [f"<td>{who}</td>"]
        content += [f"<td>{tapback}</td>"]
        content += [f'<td class="{whose_text}">{text}</td>']

        content += ["</tr>"]

    content += ["</table>"]
    content += ["</body>"]
    content += ["</html>"]

    content = "".join(content)
    return content


# /////////////////////////////////////////////////////////////// text results


def message_count_header(search):
    num_messages = count_messages(search)
    matching = "" if search_all(search) else f" matching /{search}/"

    line = f"{num_messages} messages{matching}"
    if num_messages > page_size:
        line += f".  Showing only {page_size}"
    line += "."

    return [line, ""]


def text_content(rows, search):
    columns = int(os.environ.get("COLUMNS", default_text_columns))
    fixed_columns = 88  # num columns dedicated to all fields except the last, "text"
    text_columns = columns - fixed_columns
    dashes = "-" * text_columns

    content = message_count_header(search)

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


# /////////////////////////////////////////////////////////////// database queries


def where_clause(search=None):
    where = ""

    if not search_all(search):
        where = f"where text regexp '{search}'"

    return where


def messages_count_sql(search=None):
    where = where_clause(search)
    return f"select count(*) from message {where}"


def create_message_view_sql():
    return f"""
        create view if not exists numbered_message as
        select  row_number() over(order by m.date desc, c.service_name, c.chat_identifier) row_num,
                datetime(m.date/1000000000  + strftime('%s','2001-01-01'), 'unixepoch', 'localtime') dt,
                c.service_name,
                c.chat_identifier,
                m.is_from_me,
                m.associated_message_type tapback,
                ifnull(m.text, "") text
          from  message m
                left join chat_message_join cmj on (cmj.message_id = m.ROWID)
                left join chat c on (c.ROWID = cmj.chat_id)
      group by  m.guid
    """
# we use left join because some messages are not associated with a chat
# we group by m.guid to take the first message only in case a message
# is associated with more than one service_name and/or chat_identifier


def drop_message_view_sql():
    return "drop view if exists numbered_message"


def query_offset(page=None):
    offset = ""

    if page:
        row_offset = (page - 1) * page_size
        offset = f"offset {row_offset}"

    return offset


def messages_sql(search=None, page=None):
    offset = query_offset(page)

    if search_all(search):
        return f"""
            select  *
              from  numbered_message
             limit  {page_size} {offset}
        """

    return f"""
        select  *
          from  (
                    select  m2.*,
                            m2.row_num - m1.row_num match_offset,
                            m1.match_index
                      from  (
                                select  row_number() over(order by row_num) match_index,
                                        *
                                  from  numbered_message
                                 where  text regexp '{search}'
                                 limit  {page_size} {offset}
                            ) m1,
                            numbered_message m2
                     where  m2.row_num between m1.row_num - {num_context_messages}
                                           and m1.row_num + {num_context_messages}
                  order by  m2.row_num, abs(match_offset)
                )
      group by  row_num
    """
# we use row_number() again to get the index of the matching row
# we join numbered_message with itself to capture context messages
# match_offset indicates the offset of the message from the message matching a search criteria
# match_offset is 0 for a matching message, -1 and 1 for messages surrounding it, -2 and 2 for the next,...
# match_index is the index of the matching message with respect to all matching messages
# we add abs(match_offset) to the order to ensure a row that is a match precedes one that is just context
# we group by row_num to take the first message only, in case a message appears multiple times


# /////////////////////////////////////////////////////////////// database access


def regexp(pattern, value):
    if value is None:
        return False
    return re.search(pattern, value, re.IGNORECASE) is not None


def open_database():
    home = os.environ["HOME"]
    chat_db = f"{home}/Library/Messages/chat.db"
    conn = sqlite3.connect(chat_db)
    conn.create_function("REGEXP", 2, regexp)
    return conn


def count_messages(search=None):
    db = open_database()
    cursor = db.cursor()
    cursor.execute(create_message_view_sql())
    cursor.execute(messages_count_sql(search))
    rows = cursor.fetchall()
    cursor.execute(drop_message_view_sql())

    return rows[0][0]


def select_messages(type, search=None, page=1):
    db = open_database()
    cursor = db.cursor()
    cursor.execute(create_message_view_sql())
    cursor.execute(messages_sql(search, page))
    rows = cursor.fetchall()
    cursor.execute(drop_message_view_sql())

    if type == 'html':
        content = html_content(rows, search, page)
    else:
        content = text_content(rows, search)

    return content


# /////////////////////////////////////////////////////////////// main


def text_query():
    search = sys.argv[1] if len(sys.argv) > 1 else None
    page = sys.argv[2] if len(sys.argv) > 2 else 1
    print(select_messages('text', search, int(page)))


if __name__ == '__main__':
    text_query()
