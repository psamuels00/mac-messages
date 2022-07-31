#!/bin/sh

# a collection of ad hoc queries used to understand the schema

. "`dirname $0`"/db.sh
export FORMAT=table

xdb "drop view if exists numbered_message"
xdb "create view if not exists numbered_message as
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
            join chat_message_join cmj on (cmj.message_id = m.ROWID)
            join chat c on (c.ROWID = cmj.chat_id)
    "
db "drop view if exists numbered_message"
db "create view if not exists numbered_message as
    select  row_number() over(order by m.date desc, c.service_name, c.chat_identifier) row_num,
            datetime(m.date/1000000000  + strftime('%s','2001-01-01'), 'unixepoch', 'localtime') dt,
            c.service_name,
            c.chat_identifier,
            case m.is_from_me
                when 1 then '🤓'
                else '🐵'
            end who,
            m.associated_message_type tapback,
            m.text,
            m.guid
      from  message m
            left join chat_message_join cmj on (cmj.message_id = m.ROWID)
            left join chat c on (c.ROWID = cmj.chat_id)
  group by  m.guid
    "

db "select count(*) a, count(guid) b, count(distinct guid) c from message"
db "select count(*) a, count(guid) b, count(distinct guid) c from numbered_message"

xdb "select count(*) from message where not exists (select * from chat_message_join where message_id = message.rowid)"
xdb "
    select  datetime(m.date/1000000000  + strftime('%s','2001-01-01'), 'unixepoch', 'localtime') dt,
            case m.is_from_me
                when 1 then '🤓'
                else '🐵'
            end who,
            m.associated_message_type tapback,
            m.text
      from  message m
     where  not exists (
                select * from chat_message_join where message_id = m.rowid
            )
    "

xdb "use view" "
    select  *
      from  numbered_message
     where  text like '%dog%'
     limit  5
    "


xdb "select  count(*) count_message
      from  message
   "


xdb "
    select  count(*) count_numbered_message
      from  numbered_message
   "


xdb 'messages with duplicate guid' "
    select  m.guid, count(*)
      from  message m
  group by  m.guid
    having  count(*) > 1
   "


xdb 'messages with duplicate rowid' "
    select  m.rowid, count(*)
      from  message m
  group by  m.rowid
    having  count(*) > 1
   "


xdb 'messages with duplcate guid after joining with chat' "
select count(*) from (
    select  m.guid, count(*)
      from  message m
            join chat_message_join cmj on (cmj.message_id = m.ROWID)
            join chat c on (c.ROWID = cmj.chat_id)
  group by  m.guid
    having  count(*) > 1
)
   "


xdb 'messages with duplcate rowid after joining with chat' "
select count(*) from (
    select  m.rowid, count(*)
      from  message m
            join chat_message_join cmj on (cmj.message_id = m.ROWID)
            join chat c on (c.ROWID = cmj.chat_id)
  group by  m.rowid
    having  count(*) > 1
)
   "


xdb 'sample messages' "
    select  *
      from  numbered_message
     limit  5
   "

xdb "
    select  guid
      from  numbered_message m
  group by  guid
    having  count(*) = 1
     limit  10
   "

xdb "
    select  guid
      from  numbered_message m
  group by  guid
    having  count(*) > 2
     limit  2
   "

xdb "select * from numbered_message where guid = '61383D58-B1A5-4EBD-AAD9-5476AB11C1EE'"

xdb "
    select  ROWID,guid,'text',replace,service_center,handle_id,subject,country,'attributedBody',version,type,service,account,account_guid,error,date,date_read,date_delivered,is_delivered,is_finished,is_emote,is_from_me,is_empty,is_delayed,is_auto_reply,is_prepared,is_read,is_system_message,is_sent,has_dd_results,is_service_message,is_forward,was_downgraded,is_archive,cache_has_attachments,cache_roomnames,was_data_detected,was_deduplicated,is_audio_message,is_played,date_played,item_type,other_handle,group_title,group_action_type,share_status,share_direction,is_expirable,expire_state,message_action_type,message_source,associated_message_guid,balloon_bundle_id,payload_data,associated_message_type,expressive_send_style_id,associated_message_range_location,associated_message_range_length,time_expressive_send_played,'message_summary_info',ck_sync_state,ck_record_id,ck_record_change_tag,destination_caller_id,sr_ck_sync_state,sr_ck_record_id,sr_ck_record_change_tag,is_corrupt,reply_to_guid,sort_id,is_spam,has_unseen_mention,thread_originator_guid,thread_originator_part,syndication_ranges,was_delivered_quietly,did_notify_recipient,synced_syndication_ranges
      from  message
     where  guid in (
                select  guid
                  from  numbered_message m
              group by  guid
                having  count(*) = 1
                 limit  10
            )

            or

            guid in (
                select  guid
                  from  numbered_message m
              group by  guid
                having  count(*) > 1
                 limit  2
            )
"
xdb "select chat_identifier, count(*) from chat group by chat_identifier"

