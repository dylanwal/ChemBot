https://mermaid.js.org/config/theming.html

%%{
    init: {
    'theme':'base',
    'themeVariables': {
        'background': '#414C54',
        'fontFamily': 'arial',
        'primaryColor': '#33658A',
        'primaryTextColor': '#fff',
        'primaryBorderColor': '#000000',
        'lineColor': '#F6AE2D',
        'tertiaryColor': '#AFC5D5',
        'tertiaryTextColor': '#000000'
    }
    }
}%%

https://coolors.co/001219-005f73-0a9396-94d2bd-e9d8a6-ee9b00-ca6702-bb3e03-ae2012-9b2226  

```mermaid
%%{
    init: {
    'theme':'base',
    'themeVariables': {
        'background': '#404e4d',
        'fontFamily': 'arial',
        'primaryColor': '#005f73',
        'primaryTextColor': '#ffffff',
        'primaryBorderColor': '#000000',
        'lineColor': '#ca6702',
        'tertiaryColor': '#fdf0d5',
        'tertiaryTextColor': '#000000'
    }
    }
}%%
flowchart LR

    chemicals:::chem 
    gas:::chem
    pump_1
    pump_2
    pump_3
    pump_4
    reactor
    valve_1
    valve_2
    valve_3
    valve_4
    valve_5
    LEDS
    fraction_collector
    pico_1

    %% chemical connections
    chemicals ==> valve_1
    chemicals ==> valve_2
    gas ==> valve_3
    pump_1 ==> valve_1
    valve_1 ==> tee_1
    pump_2 ==> valve_2
    valve_2 ==> tee_2
    pump_3 ==> valve_3
    valve_3 ==> tee_1
    tee_1 ==> tee_2
    tee_2 ==> reactor
    reactor ==> IR
    IR ==> valve_4
    valve_4 ==> valve_5
    pump_4 ==> valve_5
    valve_5 ==> SEC
    valve_4 ==> fraction_collector
    LEDS --- reactor

    %% computers
    subgraph computer_1  
        serial_line_pump_1
        serial_line_pump_2
        serial_line_pico_1
        serial_line_pico_2 
        USB_1
        ethernet_1
    end

    subgraph computer_2
        USB_2 
        ethernet_2
    end
    
    %% data connections
    USB_2 -.-> SEC
    serial_line_pump_1 -.-> pump_1
    serial_line_pump_1 -.-> pump_2
    serial_line_pump_1 -.-> pump_4
    serial_line_pump_2 -.-> pump_3
    serial_line_pico_1 -.-> pico_1
    pico_1 -.-> LEDS
    pico_1 -.-> valve_1
    pico_1 -.-> valve_2
    pico_1 -.-> valve_3
    pico_1 -.-> valve_4
    pico_1 -.-> valve_5
    serial_line_pico_2 -.-> fraction_collector
    USB_1 -.-> IR
    
    ethernet_1 <-.-> ethernet_2
    
    %% linkStyle 1,2,3 stroke-width:6px,stroke:red;
    classDef chem fill:#758E4F
```

```mermaid
%%{
    init: {
    'theme':'base',
    'themeVariables': {
        'background': '#404e4d',
        'fontFamily': 'arial',
        'primaryColor': '#005f73',
        'primaryTextColor': '#ffffff',
        'primaryBorderColor': '#000000',
        'lineColor': '#ca6702',
        'tertiaryColor': '#fdf0d5',
        'tertiaryTextColor': '#000000'
    }
    }
}%%
flowchart LR

    error:::error
    status:::error
    controller
    pump1,2,4
    pump_3
    valve1-5
    serial_line_pump_1:::output
    serial_line_pump_2:::output
    serial_line_pico_1:::output
    serial_line_pico_2:::output
    LEDS
    IR:::output
    SEC:::output
    fraction_collector
     
    controller
    GUI:::GUI
    
    scheduler --> controller
    
    controller --> fraction_collector
    fraction_collector --> serial_line_pico_2
    controller --> pump1,2,4 --> serial_line_pump_1
    controller --> pump_3 --> serial_line_pump_2
    controller --> valve1-5 --> serial_line_pico_1
    controller --> LEDS --> serial_line_pico_1
    controller --> IR
    controller --> SEC
    
    status --> GUI
    error --> GUI
    GUI --> scheduler
    GUI <--> data_logger
    
    scheduler --> data_logger
    controller --> tempature_probes
    tempature_probes --> serial_line_pico_1
    tempature_probes --> data_logger 
    IR --> data_logger
    SEC --> data_logger


    classDef chem fill:#758E4F
    classDef GUI fill:#758E4F
    classDef error fill:#9b2226
    classDef output fill:#94d2bd,color:#000000
```



```mermaid
%%{
    init: {
    'theme':'base',
    'themeVariables': {
        'background': '#404e4d',
        'fontFamily': 'arial',
        'primaryColor': '#005f73',
        'primaryTextColor': '#ffffff',
        'primaryBorderColor': '#000000',
        'lineColor': '#ca6702',
        'tertiaryColor': '#fdf0d5',
        'tertiaryTextColor': '#000000'
    }
    }
}%%
flowchart LR

    rabbitMQ:::rabbit    
    error:::error <--> rabbitMQ
    status:::error <--> rabbitMQ
    controller <--> rabbitMQ
    pumps <--> rabbitMQ
    valves <--> rabbitMQ
    serial_line_pump:::output <--> rabbitMQ
    serial_line_pico:::output <--> rabbitMQ
    rabbitMQ <--> LEDS
    rabbitMQ <--> IR:::output
    rabbitMQ <--> SEC:::output
    rabbitMQ <--> fraction_collector
     
    rabbitMQ <--> controller
    rabbitMQ <--> GUI:::GUI
    
    classDef rabbit fill:#001219
    classDef chem fill:#758E4F
    classDef GUI fill:#758E4F
    classDef error fill:#9b2226
    classDef output fill:#94d2bd,color:#000000
```
