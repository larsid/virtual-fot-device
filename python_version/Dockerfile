# --- Estágio 1: Base Python ---
FROM python:3.10-slim

LABEL maintainer="larsid <larsid@ecomp.uefs.br>"

# Instala as ferramentas de rede
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    tcpdump \
    iperf \
    busybox \
    iproute2 \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho DENTRO do container
WORKDIR /opt/app

# Copia o arquivo de dependências primeiro
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia TODOS os seus arquivos (.py, .json, pastas)
# para o diretório de trabalho /opt/app
COPY . .

# Define o comando para iniciar a aplicação
# Como nosso WORKDIR é /opt/app, basta chamar "main.py"
ENTRYPOINT ["python", "main.py"]
