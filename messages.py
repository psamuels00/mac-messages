#!/usr/bin/env python

from flask import Flask

import os
import sqlite3
import sys


num_messages_limit = 10
app = Flask(__name__)


# /////////////////////////////////////////////////////////////// HTTP endpoints


@app.route("/")
def hello():
    return """
        Hello, World!<br/>
        <br/>
        Try an endpoint:
        <ul>
            <li><a href="/message/count">count</a> - total number of messages</li>
            <li><a href="/message">most recent</a> - most recent messages</li>
            <li><a href="/message/dog">dog</a> - messages containing "dog"</li>
            <li><a href="/message/aristotle">aristotle</a> - messages containing "aristotle"</li>
            <li><a href="/message/socrates">socrates</a> - messages containing "socrates"</li>
        </ul>
    """


@app.route("/message/count")
def message_count():
    return str(count_messages())


@app.route("/message")
def message():
    return select_messages('html')


@app.route("/message/<search>")
def message_search(search):
    return select_messages('html', search)


# /////////////////////////////////////////////////////////////// HTML output


def message_count_div(search):
    num_messages = count_messages(search)

    content = ["<div style='margin-bottom: 1em;'>"]

    matching = f" matching /{search}/" if search else ""
    content += [f"{num_messages} messages{matching}."]

    if num_messages > num_messages_limit:
        style = "color: #B0B0B0; margin-left: 1em;"
        content += [f"<span style='{style}'>Showing only the most recent {num_messages_limit}.</span>"]

    content += ["</div>"]

    return content


def html_content(rows, search):
    content = []

    content += ["<html>"]
    content += ["<body>"]
    content += message_count_div(search)
    content += ['<table cellspacing="0" cellpadding="5" border="1">']

    content += ["<tr>"]
    for label in ("date/time", "service name", "chat id", "originator", "tapback", "text"):
        content += [f"<th>{label}</th>"]
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
    if num_messages > num_messages_limit:
        line += f".  Showing only the most recent {num_messages_limit}"
    line += "."

    return [line, ""]


def text_content(rows, search):
    content = []

    content += message_count_header(search)

    content += [f"date/time            service_name  chat_id       originator  tapback  text"]
    content += [f"-------------------  ------------  ------------  ----------  -------  ----------------------"]
    for row in rows:
        date, service_name, chat_id, originator, tapback, text = row
        content += [f"{date}  {service_name:12}  {chat_id:12}  {originator:9}  {tapback:7}  {text:80}"]

    content = "".join([f"{line}\n" for line in content])
    return content


# /////////////////////////////////////////////////////////////// database queries


def search_where_clause(search):
    return f"where text like '%{search}%'" if search else ""


def messages_count_sql(search=None):
    where = search_where_clause(search)
    return f"select count(*) from message {where}"


def messages_sql(search=None):
    where = search_where_clause(search)
    return f"""
        select  datetime(m.date/1000000000  + strftime('%s','2001-01-01'), 'unixepoch', 'localtime') ,
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
         limit  {num_messages_limit}
    """


# /////////////////////////////////////////////////////////////// database access


def open_database():
    home = os.environ["HOME"]
    chat_db = f"{home}/Library/Messages/chat.db"
    db = sqlite3.connect(chat_db)
    return db


def count_messages(search=None):
    db = open_database()
    cursor = db.cursor()
    cursor.execute(messages_count_sql(search))
    rows = cursor.fetchall()

    return rows[0][0]


def select_messages(type, search=None):
    db = open_database()
    cursor = db.cursor()
    cursor.execute(messages_sql(search))
    rows = cursor.fetchall()

    if type == 'html':
        content = html_content(rows, search)
    else:
        content = text_content(rows, search)

    return content


# /////////////////////////////////////////////////////////////// main


def main():
    search = sys.argv[1] if len(sys.argv) > 1 else None
    print(select_messages('text', search))


if __name__ == '__main__':
    main()
