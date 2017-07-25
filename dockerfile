###############################################################
# This is a Conda/Python 3.6/GDAL build based on:
# https://hub.docker.com/r/conda/miniconda3/~/dockerfile/
###############################################################

FROM debian:jessie-slim
MAINTAINER David Eitelberg, deitelberg@blueraster.com

ENV NAME polyIntersect
ENV USER polyIntersect

RUN apt-get -qq update && apt-get -qq -y install curl bzip2 \
    && curl -sSL https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -bfp /usr/local \
    && rm -rf /tmp/miniconda.sh \
    && conda install -y python=3 conda=4.3.21 \
    && apt-get -qq -y remove curl bzip2 \
    && apt-get -qq -y autoremove \
    && apt-get autoclean \
    && rm -rf /var/lib/apt/lists/* /var/log/dpkg.log \
    && conda clean --all --yes

ENV PATH /opt/conda/bin:$PATH

RUN groupadd $USER && useradd -g $USER $USER -s /bin/bash

RUN conda update conda
RUN conda config --add channels conda-forge 
RUN conda install virtualenv gunicorn gevent numpy gdal geojson urllib3

RUN mkdir -p /opt/$NAME
RUN cd /opt/$NAME && virtualenv venv && /bin/bash -c "source venv/bin/activate"
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