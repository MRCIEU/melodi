#!/bin/sh

# wait for RabbitMQ server to start
sleep 10

cd django_project 
# run Celery worker for our project myproject with Celery configuration stored in Celeryconf
su -m myuser -c "celery worker -A melodi.celery_tasks -Q default -n default@%h" 
