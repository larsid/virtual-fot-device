# Virtual-fot-device
Um dispositivo virtual capaz de simular sensores e de se comunicar através de um 
broker MQTT utilizando algumas das primitivas do protocolo TATU e ExtendedTATU.

## Sumário
- [Inicialização](#inicialização)
- [Tópicos](#tópicos)
- [Métodos compatíveis](#métodos-compatíveis)
- [Exemplo de request](#exemplos-de-request)
  - [GET](#get)
  - [FLOW](#flow)
  - [SET](#set)
  - [CONNECT](#connect)
- [Persistêcia](#persistência)
- [Logs da conexão MQTT](#logs-da-conexão-mqtt)

# Inicialização
Se nenhum argumento for informado durante a incialização o dispositivo virtual irá se conectar
ao ``localhost`` utilizando a porta ``1883``. Todavia, é possível alterar essas informações
passando os seguintes paramentros de inicialização:

| ARG | Significado | Descrição| Padrão |
|-----|-------------|----------|--------|
|**-di**| Device ID | Define o nome utilzado pelo dispositivo na identificação da conexão MQTT| Aleatório |
|**-bi**| Broker IP | Define o IP do broker MQTT | localhost|
|**-pt**| Port     | Define a porta da conexão MQTT | 1883 |
|**-us**| Username  | Define o usuário da conexão | karaf |
|**-pw**| Password     | Define a senha de conexão do broker | karaf |
|**-ps**| Persistência | Define se o dispositivo deve persistir em arquivo as amostras coletadas | true |
<!--|**-to**| Timeout | Define o tempo inicial de espera para confirmação do broker | 10.000 ms|-->

  > Atenção: Não pode haver 2 dispositivos com o mesmo device ID em um mesmo broker.

Após estabelecer a conexão com o broker o dispositivo irá enviar uma mensagem do tipo [CONNECT](#connect) 
no tópico ``dev/CONNECTION`` e aguardará por uma resposta do tipo CONNACK. Caso a resposta não 
chegue dentro de um timeout (definido como padrão em 10S) o dispositivo irá finalizar. 
Caso contário o device funcionará normalmente aguardando por solicitações [compatíveis](#métodos-compatíveis).

# Tópicos 
Este dispositivo virtual recebe requisições no tópico ``dev/DEVICE_ID`` e
responde no ``dev/DEVICE_ID/RES``.

  > Atenção: No protocolo MQTT os tópicos ``my/topic`` e ``my/topic/`` são distintos.
  > Por isso, CUIDADO quando for se inscrever ou publicar.

# Métodos compatíveis

| Método  | Compatível |
|---------|------------|
| GET     | SIM        |
| FLOW    | SIM        |
| EVT     | NÃO        |
| POST    | SIM        |
| SET     | PARCIAL    |
| CONNECT | SIM        |

# Exemplos de request
### GET
    GET VALUE sensorName
    
### FLOW
    FLOW VALUE sensorName {"publish": int, "collect":int}
       
  > Para interromper o fluxo de dados, faça uma nova requisição utilizando um valor
  > de ``publish_time`` ou ``collect_time`` menor ou igual a zero. 

### SET
Atualmente este dispositivo somente é capaz de responder a seguinte solicitação
do tipo SET.
  
    SET VALUE brokerMqtt {"id":"String", "url":"String", "port":"int", "user":"String", "password":"String"}
    
O parâmetro id é utilizado pelo cliente MQTT como identificador da conexão. Esse parâmetro, por padrão
é concatenado com o sufixo ``_CLIENT``. Já o ``url`` corresponde ao tipo da conexão (udp:// ou tcp://) + ip do
broker, caso seja passado apenas o ip do broker o dispositivo automaticamente irá por o prefixo "tcp://". 


### CONNECT

As solicitações do tipo ``CONNECT`` devem ser enviadas para o tópico ``dev/CONNECTIONS``
e são respondidas no tópico ``dev/CONNECTIONS/RES``.

    CONNECT VALUE BROKER 
    {
       "HEADER":{
                 "NAME":"String",
                 "SOURCE_IP": "String"
                 },
       "DEVICE":{
                  "id":"String",
                  "sensors":Sensor[],
                  "longitute":"long",
                  "latitude":"long"
                }
       "TIME_OUT":"Double"
    }
  
O ``TIME_OUT`` é utilizado para informar ao getaway quanto tempo o dispositivo está disposto
a esperar resposta se pode ou não efetuar a transição de getaways. 
  
O dispositivo ao enviar uma mensgem do tipo ``CONNECT`` espera receber uma mensagem do tipo 
``CONNACK`` com o seguinte formato:

```json
    {
      "CODE":"POST",
      "METHOD":"CONNACK",
      "HEADER":{"NAME":"String"},
      "BODY":{"NEW_NAME":"String", "CAN_CONNECT":"Boolean"}
    }
```
# Persistência

O dispositivo armazena todos os dados gerados pelos sensores em um arquivo que é nomeado pelo 
``deviceId``+``.csv``. Esse arquivo pode ser encontrado na mesma pasta onde a aplicação
foi executada.

Os as amostras coletados são armazenados o padrão abaixo:  

| timstamp | device id | sensor id | dados ... |
|----------|-----------|-----------|-----------|

O ``timestamp`` armazenado corresponde ao momento em as amostras foram enviadas para o 
getaway e não o tempo em que a amostra foi coletada. Já as colunas que sucedem a coluna 
``sensor id`` é considerado como uma amostra coletada pelo sensor.

Para evitar muitas operações em disco o dispositivo faz uso de um buffer
e somente inicia uma operação de escrita em arquivo após ter este buffer totalmente cheio..

# Logs da conexão MQTT

Quando um dispositivo estabelece a conexão TCP com o broker MQTT, ele grava no `stdout` uma
mensagem informando qual endereço IP local foi escolhido para aquela sessão. O log é emitido no
nível `INFO` com o seguinte formato:

```
Device <DEVICE_ID> established MQTT connection <LOCAL_IP>:<LOCAL_PORT> -> <BROKER_IP>:<BROKER_PORT>
```

Para visualizar, execute o dispositivo normalmente (por exemplo, com `java -jar target/virtual-device.jar`)
e acompanhe a saída do processo — a linha acima aparecerá logo após o `CONNECT` ser concluído.

