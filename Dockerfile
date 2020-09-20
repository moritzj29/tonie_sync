FROM python:latest

ENV TZ=Europe/Berlin
RUN mkdir /tonie
RUN mkdir /sync
VOLUME /sync
RUN apt update && apt install -y \
    ffmpeg \
    tzdata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /tonie
RUN git clone https://github.com/moritzj29/tonie_api
RUN git clone https://github.com/moritzj29/tonie_sync
RUN pip install ./tonie_api
RUN pip install ./tonie_sync

ARG TONIEBOX_SYNC_LOGLEVEL="INFO"
ARG TONIEBOX_SYNC_INTERVAL=5

# CMD not in JSON form [], to allow expansion of variables
#
# -u to not stop docker during time.sleep:
# https://stackoverflow.com/questions/42223834/docker-stucks-when-executing-time-sleep1-in-a-python-loop
CMD python -u /tonie/tonie_sync/start.py --directory=/sync --loglevel=${TONIEBOX_SYNC_LOGLEVEL} --interval=${TONIEBOX_SYNC_INTERVAL}