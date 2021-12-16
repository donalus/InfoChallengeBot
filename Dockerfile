FROM python:3.10-alpine AS pybase
WORKDIR /app

# These are required for the pycord[speed] extensions
RUN apk update && apk upgrade && \
    apk add cargo gcc g++ libffi-dev

RUN pip3 install --upgrade pip

# Install all Python requirements
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY ./pycord /app/pycord
WORKDIR /app/pycord
RUN pip3 install -U .[speed]

FROM pybase AS botrunner
COPY . /app

WORKDIR /app
CMD [ "python3", "./bot.py" ]