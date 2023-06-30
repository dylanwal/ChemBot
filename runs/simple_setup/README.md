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
    pico_2

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
        usb_pump_1 
        usb_pump_2
        usb_pump_3  
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
    usb_pump_1 -.-> pump_1
    usb_pump_2 -.-> pump_2
    usb_pump_3 -.-> pump_4
    serial_line_pump_2 -.-> pump_3
    serial_line_pico_1 -.-> pico_1
    pico_1 -.-> LEDS
    pico_1 -.-> valve_1
    pico_1 -.-> valve_2
    pico_1 -.-> valve_3
    pico_1 -.-> valve_4
    pico_1 -.-> valve_5
    pico_2 -.-> fraction_collector
    USB_1 -.-> IR
    serial_line_pico_2 -.-> pico_2
    
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


    master_controller:::error
    pump1
    pump2
    pump3
    valve1
    serial_line_pump1:::output
    serial_line_pump2:::output
    serial_line_pump3:::output
    serial_line_pico1:::output    
    IR:::output
    SEC:::output
    fraction_collector
    GUI:::GUI
        
    master_controller --> fraction_collector
    fraction_collector --> serial_line_pico3:::output 
    master_controller --> pump1 --> serial_line_pump1:::output 
    master_controller --> pump2 --> serial_line_pump2:::output 
    master_controller --> pump3 --> serial_line_pump3:::output 
    master_controller --> valve1 --> serial_line_valve:::output 
    master_controller --> valve2 --> serial_line_valve:::output 
    master_controller --> valve3 --> serial_line_valve:::output 
    master_controller --> LED_red --> serial_line_LED:::output 
    master_controller --> LED_blue --> serial_line_LED:::output 
    master_controller --> LED_green --> serial_line_LED:::output 
    master_controller --> IR
    master_controller --> SEC
    
    GUI --> master_controller
    
    master_controller --> tempature_probes
    tempature_probes --> serial_line_pico1


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
    
    pump1 <--> rabbitMQ
    pump2 <--> rabbitMQ
    pump3 <--> rabbitMQ
    valve1 <--> rabbitMQ
    valve2 <--> rabbitMQ
    valve3 <--> rabbitMQ
    fraction_collector <--> rabbitMQ
    LEDS <--> rabbitMQ

    rabbitMQ <--> master_controller:::error 
    rabbitMQ <--> GUI:::GUI
    rabbitMQ <--> IR:::output
    rabbitMQ <--> SEC:::output
    rabbitMQ <--> serial_line_pump1:::output
    rabbitMQ <--> serial_line_pump2:::output 
    rabbitMQ <--> serial_line_pump3:::output 
    rabbitMQ <--> serial_line_LED:::output 
    rabbitMQ <--> serial_line_valves:::output 
    
    classDef rabbit fill:#001219
    classDef chem fill:#758E4F
    classDef GUI fill:#758E4F
    classDef error fill:#9b2226
    classDef output fill:#94d2bd,color:#000000
```

# LED job

```mermaid
stateDiagram-v2

    state software {
    Job --> JobSubmitter
    JobSubmitter --> Master_controller
    Master_controller --> JobSubmitter
    Master_controller --> Master_controller : event_loop

    state fork_state <<fork>>
        Master_controller --> fork_state
        fork_state --> LED_red
        
        fork_state --> LED_blue
        fork_state --> LED_green
        LED_red --> Serial
        LED_blue --> Serial
        LED_green --> Serial
        LED_red --> LED_red : event_loop
        LED_blue --> LED_blue : event_loop
        LED_green --> LED_green : event_loop
        Serial --> Serial : event_loop
        
    }

    state Pico_software {
        event_loop --> event_loop
        }
    
    state Hardware {
        Pico --> LED_Drivers
        Pico --> LED_Drivers
        Pico --> LED_Drivers
        Pico --> LED_Drivers
        Pico --> LED_Drivers
        Pico --> LED_Drivers
        power_supply --> LED_Drivers
        AC_power --> power_supply
    }

    Serial --> Pico_software
    Pico_software --> Pico

```


stateDiagram-v2

    
    state Master_controller {
        [*] --> check_messages
        state if_state <<choice>>
        check_messages --> if_state
        if_state --> check_schedule
        check_schedule --> check_deactivation 
        check_deactivation --> check_messages
        check_deactivation --> [*]
        
        --
        if_state --> process_action
        state fork_state <<fork>>
            process_action --> fork_state
            fork_state --> write_add_job
            write_add_job --> validate
            validate --> schedule
            fork_state --> write_stop
            write_stop --> if_state
            schedule --> if_state
    }



    state LED {
        [*] --> 1(check_messages)
        state if_state_LED <<choice>>
        1 --> if_state_LED
        if_state_LED --> 2(check_schedule)
        2 --> 3(check_deactivation) 
        3 --> 1
        3 --> [*]
        
        --
        if_state_LED --> 4(process_action)
        state fork_state_LED <<fork>>
            4 --> fork_state_LED
            fork_state_LED --> 5(write_add_job)
            5 --> validate
            validate --> 6(schedule)
            fork_state_LED --> 7(write_stop)
            7 --> if_state_LED
            6 --> if_state_LED
    }


```mermaid
stateDiagram-v2

    
    state Master_controller {
        [*] --> check_messages
        state "check_schedule" as check_schedule
        state if_message <<choice>>
        check_messages --> if_message
        if_message --> check_schedule
        check_deactivation --> check_messages
        check_deactivation --> [*]
        state if_event <<choice>>
        check_schedule --> if_event
        if_event --> check_deactivation 
        --
        if_message --> process_action
        state fork_state <<fork>>
        process_action --> fork_state
        fork_state --> write_add_job
        write_add_job --> validate
        validate --> schedule
        fork_state --> write_stop
        write_stop --> if_message
        schedule --> if_message
    }

 
    state LED {
        state "check_messages" as 1
        state "check_profile" as 2
        state "check_deactivation" as 3
        state "process_action" as 4
        state "write_on" as 5
        state "write_stop" as 7
        state "write_power" as 8
        state "write_off" as 9

        [*] --> 1 
        state if_state_LED <<choice>>
        1 --> if_state_LED
        if_state_LED --> 2 
        2 --> 3 
        3 --> 1
        3 --> [*]
        --
        if_state_LED --> 4 
        state fork_state_LED <<fork>>
        4 --> fork_state_LED
        fork_state_LED --> 5 
        5 --> 8 
        fork_state_LED --> 7 
        7 --> 8
        fork_state_LED --> 8 
        fork_state_LED --> 9 
        8 --> if_state_LED
        9 --> 8
    }

    state Serial {
        state "check_messages" as 20
        state "write" as 21
        state "read" as 22
        state "check_deactivation" as 23
        state "process_action" as 24

        [*] --> 20
        20 --> 23
        23 --> 20
        23 --> [*]
        state if_state_serial <<fork>>
        20 --> 24
        state if_state_LED <<choice>>
        21 --> 20
        22 --> 20
        --
        24 --> if_state_serial
        if_state_serial --> 21
        if_state_serial --> 22

    }


    state SyringePump {
        state "check_messages" as 40
        state "check_deactivation" as 41
        state "process_action" as 42
        state "write_infuse" as 43
        state "write_withdraw" as 44

        [*] --> 40
        state if_state_pump <<fork>>
        40 --> if_state_pump
        if_state_pump--> 41
        
        40 --> 40
        40 --> [*]

    }


 

```

   if_event --> RabbitMQ
    8 --> RabbitMQ
   

# f

```mermaid
stateDiagram-v2

    
    state Master_controller {
        [*] --> check_messages
        state "check_schedule" as check_schedule
        state if_message <<choice>>
        check_messages --> if_message
        if_message --> check_schedule
        check_deactivation --> check_messages
        check_deactivation --> [*]
        state if_event <<choice>>
        check_schedule --> if_event
        if_event --> check_deactivation 
        --
        if_message --> process_action
        state fork_state <<fork>>
        process_action --> fork_state
        fork_state --> write_add_job
        write_add_job --> validate
        validate --> schedule
        fork_state --> write_stop
        write_stop --> if_message
        schedule --> if_message
        
        if_event --> run_event
        --
        run_event--> if_event
    }
```