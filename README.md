# mac-messages
Search through messages on a Mac using regular expressions.

## Preparation

### Set up a virtual environment

Using pyenv, for example:

    pyenv virtualenv 3.7.3 mac-messages
    pyenv local mac-messages

### Create link to messages database

    ln -s $HOME/Library/Messages/chat.db .

### Install packages

    pip install -r requirements.txt

## Run from command line

    ./messages.py [pattern] [page] [page-size] [context-size]

All arguments are optional.  The default pattern is "-" to search for all messages.
Any other value is taken as a regular expression and used to filter messages.
Results are paged.  Page 1 is displayed by default, using a page size of 10.  If
a pattern is supplied other than "-", then messages surrounding matched messages
may be displayed as well.  Context messages are disabled by default using a context
size of 0.

For example, to display the first 20 messages containing a word beginning or ending
with "dog":

    ./messages.py '\w+dog|dog\w+' 20

To display the 3rd page of messages beginning with "Good", 100 per page, including
up to 2 context messages before and after matching messages:

    ./messages.py ^good 3 100 2

## Run Web server

    ./server-run.sh

In development mode, the FastAPI server will automatically reload when source files
change.  To run in development mode:

    ./server-run-dev.sh

