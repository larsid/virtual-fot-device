# --- Estágio 1: Build ---
# Usamos uma imagem oficial com Maven e JDK 11 para compilar a aplicação
FROM maven:3.8-openjdk-11 AS builder

# Define o diretório de trabalho
WORKDIR /app

# Copia o arquivo pom.xml primeiro para aproveitar o cache do Docker.
# As dependências só serão baixadas novamente se o pom.xml mudar.
COPY pom.xml .
RUN mvn dependency:go-offline -B

# Copia todo o código-fonte da sua aplicação
COPY src ./src

# Compila a aplicação e gera o .jar. Pulamos os testes no build do Docker.
RUN mvn package -B -DskipTests

# --- Estágio 2: Final ---
# Usamos uma imagem leve, apenas com o JRE e as ferramentas necessárias
FROM adoptopenjdk/openjdk11:jre-11.0.18_10-alpine

LABEL maintainer="larsid <larsid@ecomp.uefs.br>"

WORKDIR /opt

# Instala apenas as ferramentas de runtime necessárias
RUN apk add --no-cache bash tcpdump iperf busybox-extras iproute2 iputils

# Copia o .jar final, construído no estágio 'builder', para a imagem final
COPY --from=builder /app/target/virtual-fot-device-*-jar-with-dependencies.jar /opt/device.jar

# Define o comando para iniciar a aplicação
ENTRYPOINT ["java", "-jar", "device.jar"]

