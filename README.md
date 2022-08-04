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

    ./messages.py

To show messages matching a pattern, with context messages, eg:

    ./messages.py '\w+dog|dog\w+'

To show the third page of results, eg:

    ./messages.py '\w+dog|dog\w+' 3

## Run Web server

    ./server-run.sh

To run in development mode:

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
    cmessages 'dog\w+' 2 5 1

