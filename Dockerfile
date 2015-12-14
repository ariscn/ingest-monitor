FROM fpm:vivid

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv DB82666C && \
    echo 'deb http://ppa.launchpad.net/fkrull/deadsnakes/ubuntu vivid main' > /etc/apt/sources.list.d/python.list

RUN apt-get update && \
    apt-get install -y \
        python3.5-dev=3.5.0-2+vivid1 \
        python3.5-venv=3.5.0-2+vivid1

ENV SRC /src
ENV BUILD /build
ENV PKG /cog/ingest-monitor

RUN mkdir -p $PKG && \
    python3.5 -m venv $PKG

COPY requirements/ /src/requirements
RUN $PKG/bin/pip install -r $SRC/requirements/base.txt

COPY . $SRC
RUN $PKG/bin/pip install $SRC

CMD cd $SRC && \
    fpm \
        -f \
        -t deb \
        -s dir \
        -n ingest-monitor \
        -v  "$(python3.5 -c 'import versioneer; print(versioneer.get_version())')" \
        -d 'python3.5 >= 3.5' \
        --deb-upstart debian/ingest-monitor.upstart \
        conf/=/etc/ingest-monitor \
        $PKG && \
    mkdir -p $BUILD && \
    mv *.deb $BUILD
