#!/bin/bash
uvicorn --host 0.0.0.0 --port 8000 messages.routes:app
