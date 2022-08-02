#!/bin/sh

# display basic information about the chat schema

. "`dirname $0`"/db.sh

db tables '.tables'

export FORMAT=column
db message 'pragma table_info(message)'
db chat 'pragma table_info(chat)'
db chat_message_join 'pragma table_info(chat_message_join)'
