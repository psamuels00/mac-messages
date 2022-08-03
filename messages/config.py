default_context_size = 3
# num messages before and after a match to display

default_page_size = 10
# num messages or matching messages to display at once

default_text_columns = 100
# in case COLUMNS environment var not set

enable_diagnostics = False

icon_me = "🤓"
icon_you = "🐵"

tapback_map = {
    0: "",
    2000: "❤️",
    2001: "👍",
    2002: "👎",
    2003: "😆",
    2004: "❗",
    2005: "❓",
    3000: "-❤️",
    3001: "-👍",
    3002: "-👎",
    3003: "-😆",
    3004: "-❗",
    3005: "-❓",
}

# ////////////  constants not likely needing to be changed

link_stub = "~~~<<<:::@@@:::>>>~~~"
# any string not likely to be searched for, and not containing regular expression special chars

search_all_identifier = "-"
# will appear in the URL, also should be something not likely to be searched for
