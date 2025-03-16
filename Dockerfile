# Definir a imagem base
ARG BASE_IMAGE=python:3.11-slim
FROM $BASE_IMAGE as runtime-environment

CMD ["/bin/bash"]

# # Definir variáveis de ambiente para evitar problemas com pip e threads
# ENV PIP_NO_CACHE_DIR=1 \
#     PIP_DISABLE_PIP_VERSION_CHECK=1 \
#     PIP_PROGRESS_BAR=off \
#     PYTHONUNBUFFERED=1 \
#     PYTHONMALLOC=debug \
#     DEBIAN_FRONTEND=noninteractive


ENV PIP_PROGRESS_BAR=off 

ENV OPENBLAS_NUM_THREADS=16
ENV OMP_NUM_THREADS=16
ENV MKL_NUM_THREADS=16

# Atualizar pip e instalar UV
# RUN python -m ensurepip && python -m pip install --no-cache-dir -U "pip==23.2.1" "uv"

RUN apt-get update && apt-get install -y curl \
    && curl -sSL https://sdk.cloud.google.com | bash -s -- --install-dir=/usr/local --disable-prompts \
    && ln -s /usr/local/google-cloud-sdk/bin/gcloud /usr/local/bin/gcloud


RUN set -eux; \
    apt-get install -y --no-install-recommends libgl1-mesa-glx libglib2.0-0 libglib2.0-dev

# Instalar dependências do projeto
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt


# Criar usuário do Kedro
ARG KEDRO_UID=999
ARG KEDRO_GID=0
RUN groupadd -f -g ${KEDRO_GID} kedro_group && \
useradd -m -d /home/kedro_docker -s /bin/bash -g ${KEDRO_GID} -u ${KEDRO_UID} kedro_docker

WORKDIR /home/kedro_docker

COPY ./key.json /home/kedro_docker/.config/gcloud/key.json
RUN chown -R 1000:1000 /home/kedro_docker/.config/gcloud && chmod 600 /home/kedro_docker/.config/gcloud/key.json
ENV GOOGLE_APPLICATION_CREDENTIALS="/home/kedro_docker/.config/gcloud/key.json"

RUN gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS --quiet



USER kedro_docker

# Criar segunda etapa do build para copiar o código
FROM runtime-environment

# Copiar todo o código da aplicação respeitando .dockerignore
ARG KEDRO_UID=9999
ARG KEDRO_GID=0
COPY --chown=${KEDRO_UID}:${KEDRO_GID} . .

EXPOSE 8888

# Definir comando de execução padrão
# CMD ["kedro", "run"]
