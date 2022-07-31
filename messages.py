#!/usr/bin/env python

from flask import Flask

import os
import re
import sqlite3
import sys
import urllib.parse


# /////////////////////////////////////////////////////////////// configuration


enable_diagnostics = False
num_context_messages = 0
page_size = 32
search_all_identifier = "-"


# /////////////////////////////////////////////////////////////// global vars


app = Flask(__name__)


# /////////////////////////////////////////////////////////////// misc


def search_all(search):
    return search is None or search == search_all_identifier


# /////////////////////////////////////////////////////////////// HTTP endpoints


@app.route("/")
def hello():
    return menu()


@app.route("/message/count")
def message_count():
    return str(count_messages())


@app.route("/message")
def message():
    return select_messages('html')


@app.route("/message/<search>")
def message_search(search):
    return select_messages('html', search)


@app.route("/message/<search>/<int:page>")
def message_search_page(search, page):
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
                <li><a href="/message">all</a> - all messages</li>
                <li>
                    <a href="/message/dog">dog</a> - messages containing "dog"
                    ...jump to <a href="/message/dog/2">page 2</a>,
                    <a href="/message/dog/3">page 3</a>
                </li>
                <li>
                    <a href="/message/dog%5Cw%2B">dog\w+</a> - messages matching /dog\w+/
                    ...jump to <a href="/message/dog%5Cw%2B/2">page 2</a>,
                    <a href="/message/dog%5Cw%2B/3">page 3</a>
                </li>
                <li><a href="/message/aristotle">aristotle</a> - messages containing "aristotle"</li>
                <li><a href="/message/socrates">socrates</a> - messages containing "socrates"</li>
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


# /////////////////////////////////////////////////////////////// HTML output


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
        th,
        td:first-child {
            background-color: #DDD;
        }
        th, td {
            border: 1px solid black;
            padding: 3px 5px;
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
        td.not-mine {
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
    # TODO Handle the case where the search pattern is found in a URL
    if not search_all(search):
        text = re.sub(f"({search})", r'<span class="match">\1</span>', text, 0, re.IGNORECASE)
    text = re.sub(r"(https?://([^/]+)[^\s\"']*)", r'<a href="\1" target="_blank">\2</a>', text)
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
    labels = ("#", "date/time", "service name", "chat id", "originator", "tapback", "text")
    if enable_diagnostics:
        labels = ("row#", "match offset", *labels)
    for label in labels:
        content += [f'<th>{label}</th>']
    content += ["</tr>"]

    for row in rows:
        content += ["<tr>"]

        (row_num, date, service_name, chat_id, who, tapback, text, *extra) = row

        num = row_num
        if not search_all(search):
            match_offset, match_index = extra
            num = match_index if match_offset == 0 else ""
        else:
            match_offset = "?"

        text = format_message(text, search)
        whose_text = "mine" if who == "🤓" else "not-mine"

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


# /////////////////////////////////////////////////////////////// text output


def message_count_header(search):
    num_messages = count_messages(search)
    matching = "" if search_all(search) else f" matching /{search}/"

    line = f"{num_messages} messages{matching}"
    if num_messages > page_size:
        line += f".  Showing only {page_size}"
    line += "."

    return [line, ""]


def text_content(rows, search):
    content = []

    content += message_count_header(search)

    content += [f"#       date/time            service_name  chat_id                 originator  tapback  text"]
    content += [f"------  -------------------  ------------  ----------------------  ----------  -------  ----------------------"]
    for row in rows:
        (row_num, date, service_name, chat_id, who, tapback, text, *extra) = row

        num = row_num
        if not search_all(search):
            match_offset, match_index = extra
            num = match_index if match_offset == 0 else ""

        content += [f"{num:6}  {date}  {service_name:12}  {chat_id:22}  {who:9}  {tapback:7}  {text:80}"]

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
                case m.is_from_me
                    when 1 then '🤓'
                    else '🐵'
                end who,
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
    if len(sys.argv) > 1:
        text_query()
    else:
        app.run('0.0.0.0', 8085)
