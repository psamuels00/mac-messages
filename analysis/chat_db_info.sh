#!/bin/sh

# display basic information about the chat schema

. "`dirname $0`"/db.sh
export FORMAT

FORMAT=table
db tables '.tables'

FORMAT=column
db message 'pragma table_info(message)'
db chat 'pragma table_info(chat)'
db chat_message_join 'pragma table_info(chat_message_join)'

FORMAT=table
db 'most recent messages' "
        select  datetime(m.date/1000000000  + strftime('%s','2001-01-01'), 'unixepoch', 'localtime') 'date/time',
                c.service_name,
                c.chat_identifier,
                case m.is_from_me
                    when 1 then '🤓'
                    else '🐵'
                end who,
                m.associated_message_type tapback,
                substr(m.text, 0, 50) text
          from  message m
                join chat_message_join cmj on (cmj.message_id = m.ROWID)
                join chat c on (c.ROWID = cmj.chat_id)
      order by  m.date desc, c.service_name, c.chat_identifier
         limit  10
    "
