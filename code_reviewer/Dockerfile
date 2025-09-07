FROM python:3.12.11-alpine3.22

ENV VERSION="0.1.0"

RUN --mount=type=cache,target=/var/cache/apk,id=code-review-apk \
    apk add git

COPY requirements.txt /tmp
RUN --mount=type=cache,target=/root/.cache/pip,id=code-review-pip \
    pip install -r /tmp/requirements.txt

ENV PYTHONPATH=/opt
COPY app /opt/app

WORKDIR /repo

RUN git config --global --add safe.directory /repo

ENTRYPOINT ["python", "-m", "app"]
