#!/usr/bin/env python

from flask import Flask

import os
import re
import sqlite3
import sys
import urllib.parse


page_size = 10
app = Flask(__name__)


# /////////////////////////////////////////////////////////////// misc


search_all_identifier = "-"


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
            Hello, World!<br/>
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
                <li><a href="/message/aristotle">aristotle</a> - messages containing "aristotle"</li>
                <li><a href="/message/socrates">socrates</a> - messages containing "socrates"</li>
            </ul>
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
        span {
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
    </style>
    </head>
    """

def message_count_section(search):
    num_messages = count_messages(search)

    content = ["<div>"]

    matching = "" if search_all(search) else f" matching /{search}/"
    content += [f"{num_messages} messages{matching}."]

    if num_messages > page_size:
        content += [f"<span>Showing {page_size} at a time.</span>"]

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


def html_content(rows, search, page):
    content = []

    content += ["<html>"]
    content += [head_with_style()]
    content += ["<body>"]
    content += message_count_section(search)
    content += navigation_menu(search, page)
    content += ['<table>']

    content += ["<tr>"]
    for label in ("#", "date/time", "service name", "chat id", "originator", "tapback", "text"):
        content += [f'<th>{label}</th>']
    content += ["</tr>"]

    for row in rows:
        content += ["<tr>"]
        for column in row:
            content += [f"<td>{column}</td>"]
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
        rownum, date, service_name, chat_id, originator, tapback, text = row
        content += [f"{rownum:6}  {date}  {service_name:12}  {chat_id:22}  {originator:9}  {tapback:7}  {text:80}"]

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
                m.text
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

    where = where_clause(search)
    return f"""
        select  m1.*
          from  numbered_message m1
         where  m1.text regexp '{search}'
         limit  {page_size} {offset}
    """
    return f"""
        select  m1.*
          from  numbered_message m1,
                numbered_message m2
         where  m1.row_num = m2.row_num
                and m2.text regexp '{search}'
         -- where  m1.row_num between m2.row_num - 3 and m2.row_num + 3
         -- limit  {page_size} {offset}
    """


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
