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

In development mode, FastAPI will automatically reload when source files change.


## Run in Docker container

1. Install Docker
2. Allow Docker to access ~/Library/Messages (Settings > Resources > File Sharing)
3. Build the image


    docker build -t mac-messages .

### Run Web server in container

    docker run -dp 8000:8000 -v $HOME/Library/Messages:/app/db mac-messages

Commands to examine and cleanup:

    container() { docker ps | grep mac-messages | cut -d' ' -f 1; }
    docker exec -it `container` bash
    docker logs `contain`
    docker kill `contain`
    docker rmi -f mac-messages

## Run from command line in container:

    cmessages() { docker run --rm -v $HOME/Library/Messages:/app/db --env COLUMNS --entrypoint ./messages.py mac-messages $@; }
    cmessages
    cmessages 'dog\w+' 2 5 1
