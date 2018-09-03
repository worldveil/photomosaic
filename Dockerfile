# https://github.com/plippe/faiss-docker/blob/master/Dockerfile
FROM nvidia/cuda:8.0-devel-ubuntu16.04

ENV FAISS_CPU_OR_GPU "cpu"
ENV FAISS_VERSION "1.3.0"
ENV OPENCV_VERSION "3.4.1"

RUN apt-get update && apt-get install -y curl bzip2 libgl1-mesa-glx

RUN curl https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh > /tmp/conda.sh
RUN bash /tmp/conda.sh -b -p /opt/conda && \
    /opt/conda/bin/conda update -n base conda && \
    /opt/conda/bin/conda install -y -c pytorch faiss-${FAISS_CPU_OR_GPU}=${FAISS_VERSION} && \
    apt-get remove -y --auto-remove curl bzip2 && \
    apt-get clean && \
    rm -fr /tmp/conda.sh

RUN /opt/conda/bin/conda install -y -c conda-forge opencv=$OPENCV_VERSION

ENV PATH="/opt/conda/bin:${PATH}"

RUN apt-get update -y && \
        apt-get install -y \
        build-essential \
        cmake \
        git \
        wget \
        unzip \
        yasm \
        pkg-config \
        libswscale-dev \
        libtbb2 \
        libtbb-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libavformat-dev \
        libpq-dev \
        libopenblas-dev \
        liblapack3 \
        python-dev \
        swig \
        git \
        python-pip \
        tree

RUN pip install numpy pytest ipython[notebook]==5.8.0 scipy bs4 sklearn boto3 requests matplotlib cython ipdb
