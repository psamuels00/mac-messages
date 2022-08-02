from .html_out import (
    count_messages_html,
    menu_html,
    select_messages_html,
)
from fastapi import FastAPI
from fastapi.responses import HTMLResponse


app = FastAPI(default_response_class=HTMLResponse)


@app.get("/")
async def hello():
    return menu_html()


@app.get("/menu")
async def hello_menu():
    return menu_html()


@app.get("/menu/{page_size}")
async def hello_menu(page_size :int):
    return menu_html(page_size)


@app.get("/menu/{page_size}/{context_size}")
async def hello_menu(page_size :int, context_size :int):
    return menu_html(page_size, context_size)


@app.get("/message/count")
async def message_count():
    return count_messages_html()


@app.get("/message")
async def message():
    return select_messages_html()


@app.get("/message/{search}")
async def message(search):
    return select_messages_html(search)


@app.get("/message/{search}/{page}")
async def message(search, page :int):
    return select_messages_html(search, page)


@app.get("/message/{search}/{page}/{page_size}")
async def message(search, page :int, page_size :int):
    return select_messages_html(search, page, page_size)


@app.get("/message/{search}/{page}/{page_size}/{context_size}")
async def message(search, page :int, page_size :int, context_size :int):
    return select_messages_html(search, page, page_size, context_size)
