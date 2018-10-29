# use base python image with python 2.7
FROM python:2.7

# add requirements.txt to the image
ADD requirements.txt /app/requirements.txt

# set working directory to /app/
WORKDIR /app/

# install python dependencies
RUN pip install -r requirements.txt

# create unprivileged user
RUN adduser --disabled-password --gecos '' myuser

# install statsmodels
RUN easy_install statsmodels


#nginx gunicorn things

ENV PROJECT_ROOT /app

COPY start.sh /start.sh

# EXPOSE port 8000 to allow communication to/from server
EXPOSE 8000

# CMD specifcies the command to execute to start the server running.
#CMD ["/start.sh"]
# done!
