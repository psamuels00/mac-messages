from .util import search_all


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


def query_offset(page, page_size):
    offset = ""

    if page:
        row_offset = (page - 1) * page_size
        offset = f"offset {row_offset}"

    return offset


def messages_sql(search, page, page_size, context_size):
    offset = query_offset(page, page_size)

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
                     where  m2.row_num between m1.row_num - {context_size}
                                           and m1.row_num + {context_size}
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
