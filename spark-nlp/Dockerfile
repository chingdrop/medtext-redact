FROM tensorflow/tensorflow:2.7.4-gpu

# Fetch keys for apt
RUN rm /etc/apt/sources.list.d/cuda.list && \
    apt-key del 7fa2af80 && \
    apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub

RUN apt-get update -y && apt-get -y upgrade && \
    apt-get install -y \
        wget \
        jq \
        lsb-release \
        openjdk-8-jdk-headless \
        build-essential \
        python3 \
        python3-pip && \
    pip3 install --quiet --upgrade pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /usr/share/man /usr/share/doc /usr/share/doc-base

# Create Local User
ENV NB_USER johnsnow
ENV NB_UID 1000

RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    ${NB_USER}

ENV HOME /home/${NB_USER}
RUN chown -R ${NB_UID} ${HOME}

ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

USER ${NB_USER}
WORKDIR ${HOME}

EXPOSE 8888
CMD ["jupyter", "lab", "--ip", "0.0.0.0"]
