#!/bin/bash

# Exit on error
set -e

alembic revision --autogenerate -m "${1:-Auto migration}"

echo "Migration generated""