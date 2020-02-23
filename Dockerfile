FROM python:3.8.1-alpine3.11

# indicate switch for unbuffered stdin and stdout (equiv to python -u)
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/www/xero-testdata

# prep + dependancies
RUN \
   apk update && \
   apk add bash build-base libffi-dev openssl-dev python3-dev curl sudo git openssh && \
   chmod 755 .
   #rm /usr/bin/python && \
   #ln -s /usr/bin/python3 /usr/bin/python

# upgrade pip
RUN pip3 install --upgrade pip==20.0.2

# install python dependancies
COPY ./requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# add codebase
COPY . .

# run Flask web server
ENTRYPOINT ["/bin/bash", "./run.sh"]
