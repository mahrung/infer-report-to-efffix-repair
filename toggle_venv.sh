#!/bin/bash

if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Deactivating virtual environment..."
    deactivate
fi
