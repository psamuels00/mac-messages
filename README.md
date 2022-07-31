# mac-messages
Search through messages on a Mac.

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

    ./messages.py -

To show messages matching a pattern, with context messages, eg:

    ./messages.py '\w+dog|dog\w+'

## Run Web server

    ./flask-run.sh

To run in debug mode:

    ./flask-run-debug.sh

In debug mode, Flask will automatically reload when source files change.
