# Virtual-FoT-Device (Versão Python)

Um dispositivo virtual capaz de simular sensores e de se comunicar através de um broker MQTT utilizando as primitivas do protocolo TATU.

Esta é uma versão em Python do [Virtual-FoT-Device original](https://www.google.com/search?q=https://github.com/larsid/virtual-fot-device), refatorada para usar o pacote oficial [`extended-tatu-wrapper`](https://www.google.com/search?q=%5Bhttps://github.com/larsid/extended-tatu-wrapper/tree/main/python-version%5D\(https://github.com/larsid/extended-tatu-wrapper/tree/main/python-version\)) e ser executada como um container Docker.

## 🚀 Execução Rápida com Docker

Este projeto é totalmente containerizado. A única dependência é o **Docker**.

### Passo 1: Build da Imagem

Na raiz do projeto (onde está o `Dockerfile`), construa a imagem:

```bash
docker build -t virtual-fot-device-python .
```

### Passo 2: Configuração (Variáveis de Ambiente)

A configuração do dispositivo é feita via variáveis de ambiente passadas para o container. A versão em Java usava argumentos de linha de comando; esta versão usa exclusivamente o ambiente.

| Variável | Descrição | Padrão (se não definida) |
| :--- | :--- | :--- |
| `DEVICE_ID` | ID único do dispositivo no broker MQTT. | Um UUID aleatório |
| `BROKER_IP` | O IP ou hostname do broker MQTT. | `localhost` |
| `PORT` | Porta do broker MQTT. | `1883` |
| `USERNAME` | Usuário para autenticação no broker. | `karaf` |
| `PASSWORD` | Senha para autenticação no broker. | `karaf` |
| `BIND_IP` | **(Importante para Simulações)** O IP que o dispositivo deve reportar no `CONNECT`. | IP interno do container (`socket.gethostname()`) |
| `CONNECTION_TIMEOUT` | Indica o tempo do timeout de espera para o gateway permitir a conexão do device, caso seja 0 o timeout não funcionará e o device fica em espera continua. | 10 segundos de timeout |
| `API_URL` | URL da API para onde os logs de latência (RTT) são enviados. | `http://localhost:8080/api/latency-records/records` |

### Passo 3: Execução do Container

Execute o container passando as variáveis de ambiente necessárias.

```bash
docker run --rm -it \
  -e DEVICE_ID="py_device_01" \
  -e BROKER_IP="127.0.0.1" \
  -e USERNAME="karaf" \
  -e PASSWORD="karaf" \
  -e BIND_IP="10.0.0.5" \
  -e CONNECTION_TIMEOUT=0 \
  --name "py_device_01" \
  virtual-fot-device-python
```

-----

## ⚠️ Passo 4: Handshake de Conexão (Obrigatório)

Ao iniciar, o dispositivo **não** fica online imediatamente. Ele adota o fluxo de conexão estendido do TATU:

1.  O dispositivo se conecta ao broker e publica uma mensagem `CONNECT` no tópico `dev/CONNECTIONS`.
2.  Ele **aguarda 10 segundos** por uma mensagem `CONNACK` de um gateway no tópico `dev/CONNECTIONS/RES`.
3.  Se o `CONNACK` não chegar, o dispositivo entra em timeout e é encerrado (com um log CRITICAL).

**Ação Necessária:** Para que o dispositivo fique online, você (ou seu gateway simulado) deve publicar a seguinte mensagem no broker:

  * **Tópico:** `dev/CONNECTIONS/RES`
  * **Payload (Mensagem):**
    ```json
    {"CODE":"POST", "METHOD":"CONNACK", "HEADER":{"NAME":"Meu-Gateway-Simulado"}, "BODY":{"NEW_NAME":"py_device_01", "CAN_CONNECT":true}}
    ```

Após receber esta mensagem, o dispositivo se conectará permanentemente e se inscreverá no seu tópico de comandos (`dev/py_device_01`).

## 📡 Tópicos MQTT

O dispositivo utiliza os seguintes tópicos, conforme o padrão `extended-tatu-wrapper`:

  * **Tópico de Comando:** `dev/{DEVICE_ID}` (Onde o dispositivo escuta por comandos `GET`, `FLOW`, `SET`).
  * **Tópico de Resposta:** `dev/{DEVICE_ID}/RES` (Onde o dispositivo publica respostas `GET` e dados `FLOW`).
  * **Tópico de Conexão:** `dev/CONNECTIONS` (Onde o dispositivo publica sua mensagem `CONNECT` inicial).
  * **Tópico de Resposta de Conexão:** `dev/CONNECTIONS/RES` (Onde o dispositivo escuta pela resposta `CONNACK`).

## ⚙️ Métodos TATU Suportados

| Método | Suportado | Descrição |
| :--- | :--- | :--- |
| `GET` | **Sim** | Solicita o valor atual de um sensor. |
| `FLOW` | **Sim** | Inicia ou para um fluxo de dados de um sensor. |
| `SET` | **Parcial** | Suporta `SET VALUE brokerMqtt` para migração de broker. |
| `CONNECT` | **Sim** | Utilizado no handshake inicial. |
| `CONNACK` | **Sim** | Recebido como parte do handshake. |
| `EVT` | Não | |
| `POST` | Não | (O dispositivo *envia* `POST` como resposta, mas não *recebe* comandos `POST`). |

## 🕹️ Exemplos de Comandos

Para interagir com o dispositivo (após o handshake), publique as seguintes mensagens no tópico de comando (`dev/{DEVICE_ID}`):

### GET

Solicita o valor atual do `temperatureSensor`.

  * **Payload (Mensagem):**
    ```
    GET VALUE temperatureSensor
    ```
  * **Resposta (em `.../RES`):**
    ```json
    {"METHOD":"GET","CODE":"POST","HEADER":{"NAME":"py_device_01","TIMESTAMP":1678886401000},"BODY":{"temperatureSensor":18}}
    ```

### FLOW (Iniciar)

Inicia um fluxo no `humiditySensor` para coletar dados a cada 1 segundo e publicá-los a cada 5 segundos.

  * **Payload (Mensagem):**
    ```
    FLOW VALUE humiditySensor {"collect": 1000, "publish": 5000}
    ```
  * **Resposta (em `.../RES`, a cada 5s):**
    ```json
    {"METHOD":"FLOW","CODE":"POST","HEADER":{"NAME":"py_device_01","TIMESTAMP":1678886406000},"BODY":{"humiditySensor":[22,23,22,24,23],"FLOW":{"publish":5000,"collect":1000}}}
    ```

### FLOW (Parar)

Para o fluxo de dados do `humiditySensor`.

  * **Payload (Mensagem):**
    ```
    FLOW VALUE humiditySensor {"collect": 0, "publish": 0}
    ```

### SET (Migração de Broker)

Instrui o dispositivo a se desconectar do broker atual e se conectar a um novo.

  * **Payload (Mensagem):**
    ```
    SET VALUE brokerMqtt {"url":"192.168.1.100", "port":"1883", "user":"novo_user", "password":"novo_pass"}
    ```