from .config import *
from .db_access import count_messages, select_messages
from .util import search_all

import re
import urllib.parse


def count_messages_html():
    return str(count_messages(search=None))


def select_messages_html(search=None, page=1, page_size=default_page_size, context_size=default_context_size):
    rows = select_messages(search, page, page_size, context_size)
    return html_content(rows, search, page, page_size, context_size)


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
        div.title {
            font-size: 150%;
        }
        div.menu-hint {
            color: #BBB;
            margin-top: 0.5em;
            font-style: italic;
        }
        div.menu-hint a {
            color: #BBB;
            margin-left: 0.5em;
        }
        form {
            margin: 2em 0em;
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
        li a {
            font-family: monospace;
        }
        .regex {
            font-family: monospace;
            background-color: #EEE;
            padding: 2px 5px;
        }
        table { 
            border-collapse: collapse;
        }
        tr.match span {
            color: #3C3;
            font-weight: bold;
        }
        tr.context {
            color: #AAA;
            filter: grayscale(100%);
        }
        tr.context span {
            color: #9C9;
            font-weight: bold;
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
    </style>
    </head>
    """


def menu_html(page_size=default_page_size, context_size=default_context_size):
    optional = ""
    optional_num_context = ""
    reset_link = '<a href="/menu">reset</a>'
    if page_size != default_page_size and context_size != default_context_size:
        optional = f"/{page_size}/{context_size}"
        optional_num_context = f"/{context_size}"
    elif page_size != default_page_size:
        optional = f"/{page_size}"
    elif context_size != default_context_size:
        optional_num_context = f"/{context_size}"
    else:
        reset_link = ""

    min100 = ".{100,}"  # we must interpolate this value instead of including it directly
                        # in the return value since it contains brackets that would
                        # otherwise disturb the python string formattting

    # TODO Do not add search, page, page_size, or context_size to links unless necessary

    # Special cases for search value, and how they are automatically transformed:
    #
    #     value  new value
    #     -----  -------
    #            -
    #     .      .{1}
    #     ..     .{2}

    script = """
        <script>
            function form_submit(optional) {
                value = document.forms.search.search.value
                
                value = {
                    '': '-',
                    '.': '.{1}',
                    '..': '.{2}',
                }[value] || value;
                
                window.location.href = '/message/' + encodeURI(value) + '/1' + optional;
                return false;
            }
        </script>
    """

    return f"""
        <html>
        {head_with_style()}
        {script}
        <body>
            <div class="title">
                Welcome to Mac Messages
            </div>
            
            <form name="search" onsubmit="return form_submit('{optional}')">
                Search for:
                <input name="search" type="text" size="20" />
                <input type="submit" value="Submit" />
                <div class="menu-hint">
                    Using page size {page_size}, context size {context_size}. {reset_link}
                </div>
            </form>
            
            <hr />
            
            Total number of messages:
            <ul>
                <li><a href="/message/count">count</a> - total number of messages</li>
            </ul>
            
            All messages, default paging:
            <ul>
                <li><a href="/message/-/1{optional}">all</a> - all messages</li>
            </ul>
            
            Messages matching a regular expression:
            <ul>
                <li><a href="/message/dog/1{optional}">dog</a> - messages containing "dog"</li>
                <li><a href="/message/dog%5Cw%2B/1{optional}">dog\w+</a> - messages matching /dog\w+/</li>
                <li><a href="/message/%5Cw%2Adog%5Cw%2A/1{optional}">\w*dog\w*</a> - messages matching /\w*dog\w*/</li>
                <li><a href="/message/aristotle/1{optional}">aristotle</a> - messages containing "aristotle"</li>
                <li><a href="/message/socrates/1{optional}">socrates</a> - messages containing "socrates"</li>
                <li><a href="/message/godzilla/1{optional}">godzilla</a> - messages containing "godzilla"</li>
                <li><a href="/message/.%7B100%2C%7D/1{optional}">{min100}</a> - messages at least 100 characters long</li>
            </ul>
            
            Messages at a specific page of results:
            <ul>
                <li><a href="/message/-/2{optional}">all</a> - all messages, page 2</li>
                <li><a href="/message/-/7{optional}">all</a> - all messages, page 7</li>
                <li><a href="/message/dog/2{optional}">dog</a> - messages containing "dog", page 2</li>
                <li><a href="/message/dog/3{optional}">dog</a> - messages containing "dog", page 3</li>
            </ul>
            
            Custom page size:
            <ul>
                <li><a href="/message/-/1/100{optional_num_context}">all</a> - all messages, 100 per page</li>
                <li><a href="/message/dog/1/100{optional_num_context}">dog</a> - messages containing "dog", 100 per page</li>
            </ul>
            
            Custom context size:
            <ul>
                <li><a href="/message/dog/1/{page_size}/2">dog</a> - messages containing "dog", with 2 context messages before and after</li>
                <li><a href="/message/dog/1/{page_size}/1">dog</a> - messages containing "dog", with 1 context message before and after</li>
                <li><a href="/message/dog/1/{page_size}/0">dog</a> - messages containing "dog", with no context messages</li>
            </ul>
        </body>
    </html>
    """


def message_count_section(search, page_size):
    num_messages = count_messages(search)

    content = ["<div>"]

    matching = "" if search_all(search) else f' matching /<span class="regex">{search}</span>/'
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


def navigation_menu(search, page, page_size, context_size):
    if page is None:
        return ""

    num_messages = count_messages(search)
    max_page = int(num_messages / page_size) + 1
    search = search_all_identifier if search_all(search) else search
    search = urllib.parse.quote_plus(search)

    optional_home = ""
    optional = ""
    if page_size != default_page_size or context_size != default_context_size:
        optional_home = f"menu/{page_size}"
        optional = f"/{page_size}"
    if context_size != default_context_size:
        optional_home += f"/{context_size}"
        optional += f"/{context_size}"

    return "".join([
        "<div>",
            menu_option(f"/{optional_home}", "Home"),
            menu_option(f"/message/{search}/1{optional}", "&lt;&lt;"),
            menu_option(f"/message/{search}/{page-1}{optional}", "&lt;"),
            menu_option(f"/message/{search}/{page+1}{optional}", "&gt;"),
            menu_option(f"/message/{search}/{max_page}{optional}", "&gt;&gt;"),
        "</div>"
    ])


def format_message(text, search, match_offset):
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

    if not search_all(search) and match_offset == 0:
        text = re.sub(f"({search})", r'<span class="match">\1</span>', text, 0, re.IGNORECASE)

    text = re.sub(link_stub, swap_stub_with_link, text)

    return text


def html_content(rows, search, page, page_size, context_size):
    content = []

    content += ["<html>"]
    content += [head_with_style()]
    content += ["<body>"]
    content += message_count_section(search, page_size)
    content += navigation_menu(search, page, page_size, context_size)
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

        text = format_message(text, search, match_offset)
        if is_from_me:
            whose_text = "mine"
            who = icon_me
        else:
            whose_text = "yours"
            who = icon_you

        tapback = tapback_map[tapback]

        row_class = "match" if search_all(search) or match_offset == 0 else "context"
        content += [f'<tr class="{row_class}">']

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