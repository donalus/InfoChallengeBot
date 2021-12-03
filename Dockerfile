FROM python:3.9-alpine
WORKDIR /app

# Placeholder Environment Variables
ENV token=
ENV key=!

# Install all Python requirements
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . /app

CMD [ "python3", "./bot.py" ]