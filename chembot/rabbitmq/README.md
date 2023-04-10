## Installation
1) Open Powershell as Administrator
2) Install chocolatey (https://chocolatey.org/install)
3) Install RabbitMQ `choco install rabbitmq`
4) Server starts up automatically on install

## RabbitMQ
    # Navigate to location of server files
    'cd C:\Program Files\RabbitMQ Server\rabbitmq_server-3.11.13\sbin'  # version may be different

    # start server
    `.\rabbitmq-server.bat -detached`

    # stop server
    `.\rabbitmqctl.bat stop`

    # check server status
    `.\rabbitmqctl.bat status`


## checking server
http://localhost:15672/
Username: guest
Password: guest
