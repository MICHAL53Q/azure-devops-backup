FROM python:3.10-alpine3.16 as test

RUN apk add --no-cache \
    gcc \
    libc-dev \
    libffi-dev \
    git 

WORKDIR /usr/src

COPY ./app/requirements.txt ./app/

RUN pip install --no-cache-dir -r ./app/requirements.txt
RUN pip install pytest
RUN pip install mock

COPY . .

RUN pytest

FROM python:3.10-alpine3.16 as final

RUN apk add --no-cache \
    gcc \
    libc-dev \
    libffi-dev \
    git 

WORKDIR /usr/src/app

COPY --from=test /usr/src/app ./

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/usr/src

CMD [ "python", "main.py" ]
