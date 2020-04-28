FROM python:3.7

RUN apt-get update && apt-get install -y vlc

COPY requirements.txt ./
RUN pip install -r requirements.txt

ADD app /app

WORKDIR /app

# CMD ["bash"]