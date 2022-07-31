#!/bin/bash

export FLASK_APP=messages.py
export FLASK_ENV=development

flask run --port 8085
