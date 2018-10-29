#!/bin/sh

# wait for SQL server to start
sleep 10

cd django_project
# prepare init migration
su -m myuser -c "python manage.py makemigrations"
# migrate db, so we have the latest db schema
su -m myuser -c "python manage.py migrate"
# start development server on public ip interface, on port 8000
#su -m myuser -c "python manage.py runserver 0.0.0.0:8000" 
