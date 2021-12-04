FROM python:3.10-alpine
WORKDIR /app

# Install all Python requirements
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . /app

CMD [ "python3", "./bot.py" ]