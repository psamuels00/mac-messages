# usage: db <sql>
#        db <label> <sql>
#
# eg: db "select 5 * 5"
#     db "square a number" "select 5 * 5"
#
# The default output format is column, but can be changed using the FORMAT
# environment variable, to table or csv, for example, as in:
#
#     FORMAT=table db "square a number" "select 5 * 5"
#
# Comment out a db statement by renaming it to the nop function xdb:
#
#     xdb "select  ...
#            from  ...
#           where  ...
#           ...
#         "
#
db() {
    local label
    if [ -n "$2" ]; then
        label=$1
        shift
        echo $label
        echo ${label//?/=}
        echo
    fi
    local sql=${1//%/%%}

    local format=column
    if [ -n "$FORMAT" ]; then
        format=$FORMAT
    fi
    if [ "$format" = "column" ]; then
        format='column -header'
    fi

    printf "$sql" | sqlite3 -$format chat.db

    if [ -n "$label" ]; then
        echo
    fi
}

xdb() { :; }    # easily comment out a db statement by renaming it to xdb

if [ ! -e chat.db ]; then
    ln -s $HOME/Library/Messages/chat.db .
fi
