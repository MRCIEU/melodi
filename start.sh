#!/bin/bash

# Start Gunicorn processes
echo Starting Gunicorn.

#make sure we are at project root /usr/src/app
cd $PROJECT_ROOT

if [ ! -f $PROJECT_ROOT/.build ]; then
  echo "Collecting static files"
  pushd django_project
  python manage.py collectstatic --noinput
  popd
  date > $PROJECT_ROOT/.build
fi

cd django_project 
exec gunicorn melodi.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3
