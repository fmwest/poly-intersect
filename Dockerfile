FROM python:3.6-alpine
MAINTAINER David Eitelberg deitelberg@blueraster.com

ENV NAME landrights
ENV USER landrights

RUN apk update && apk upgrade && \
   apk add --no-cache --update bash git openssl-dev build-base alpine-sdk \
   libffi-dev postgresql-dev gcc python3-dev musl-dev

RUN addgroup $USER && adduser -s /bin/bash -D -G $USER $USER

RUN easy_install pip && pip install --upgrade pip
RUN pip install virtualenv gunicorn gevent

###################################################################################
#### Install GEOS ####
ENV GEOS http://download.osgeo.org/geos/geos-3.6.1.tar.bz2

ENV PROCESSOR_COUNT 1

WORKDIR /install-postgis

WORKDIR /install-postgis/geos
ADD $GEOS /install-postgis/geos.tar.bz2
RUN tar xf /install-postgis/geos.tar.bz2 -C /install-postgis/geos --strip-components=1

RUN ./configure && make -j $PROCESSOR_COUNT && make install
RUN pip install shapely
RUN pip install pyproj
RUN pip install geojson
###################################################################################

RUN mkdir -p /opt/$NAME
RUN cd /opt/$NAME && virtualenv venv && source venv/bin/activate
COPY requirements.txt /opt/$NAME/requirements.txt
RUN cd /opt/$NAME && pip install -r requirements.txt

COPY entrypoint.sh /opt/$NAME/entrypoint.sh
COPY main.py /opt/$NAME/main.py
COPY gunicorn.py /opt/$NAME/gunicorn.py

# Copy the application folder inside the container
WORKDIR /opt/$NAME

COPY ./$NAME /opt/$NAME/$NAME
COPY ./microservice /opt/$NAME/microservice
COPY ./tests /opt/$NAME/tests
RUN chown $USER:$USER /opt/$NAME

# Tell Docker we are going to use this ports
EXPOSE 5700
USER $USER

# Launch script
ENTRYPOINT ["./entrypoint.sh"]