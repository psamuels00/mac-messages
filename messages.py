#!/usr/bin/env python

from flask import Flask

import os
import re
import sqlite3
import sys
import urllib.parse


page_size = 10
app = Flask(__name__)


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

    matching = f" matching /{search}/" if search and search != "-" else ""
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
    search = "-" if search is None else search
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
    matching = f" matching /{search}/" if search else ""

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


def search_where_clause(search):
    if search == "-":
        return ""
    return f"where text regexp '{search}'" if search else ""


def messages_count_sql(search=None):
    where = search_where_clause(search)
    return f"select count(*) from message {where}"


def messages_sql(search=None, page=None):
    where = search_where_clause(search)
    offset = ""
    if page:
        row_offset = (page - 1) * page_size
        offset = f"offset {row_offset}"

    return f"""
        select  row_number() over(order by dt, service_name, chat_identifier),
                *
          from  (

                select  datetime(m.date/1000000000  + strftime('%s','2001-01-01'), 'unixepoch', 'localtime') dt,
                        c.service_name,
                        c.chat_identifier,
                        case m.is_from_me
                            when 1 then '🤓'
                            else '🐵'
                        end,
                        m.associated_message_type,
                        m.text
                  from  message m
                        join chat_message_join cmj on (cmj.message_id = m.ROWID)
                        join chat c on (c.ROWID = cmj.chat_id)
               {where}
              order by  m.date desc, c.service_name, c.chat_identifier

                )
         limit  {page_size} {offset}
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
    cursor.execute(messages_count_sql(search))
    rows = cursor.fetchall()

    return rows[0][0]


def select_messages(type, search=None, page=1):
    db = open_database()
    cursor = db.cursor()
    cursor.execute(messages_sql(search, page))
    rows = cursor.fetchall()

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
