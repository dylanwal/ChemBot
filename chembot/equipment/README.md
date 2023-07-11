# Equipment Overview

Every piece of equipment has three types of methods:
* activate
  * Only one method per equipment and is called to start the piece of equipment
  * Starts the infinite loop
  * Starts listening for RabbitMQ messages
* write_
  * Cause a change in value; or does an action
* read_
  * Returns value or data
  * Does not cause any changes in state or actions

Equipment.attrs should be updated with attributes in subclasses.




```mermaid
classDiagram

    class State {
        OFFLINE
        PREACTIVATION 
        STANDBY 
        SCHEDULED_FOR_USE 
        RUNNING 
        RUNNING_BUSY 
        SHUTTING_DOWN
        CLEANING
        ERROR 
    }

    class Rabbit {
        +string topic
        +Channal channel
        +Queue queue
        +queue_exists()
        +consume()
        +send()
        +deactivate()
        
    }

    class Equipment{
      +String class_name
      +State state
      +Rabbit Rabbit

      +activate()
      -register_equipment()
      -unregiser_equipment()
      -run()
      +read_all_attributes()
      +read_update()
      +read_state()
      +write_deactivate()
      +write_stop()
      +write_profile()
    }

    class Syringe {
        + Quantity volume
        + Quantity diameter
        + Quantity pull
        + string class_name 
    }

    class SyringePump{
      +Syring syringe
      +control_method
      -pump_state
      -volume
      -volume_dispaced
      -volume_target
      -flow_rate
      -time_running
      -time_end
      -pull
      +read_syringe()
      +write_syringe()
      +write_empty()
      +write_refill()
      +write_infuse()
      +write_withdraw()
    }


    class HarvardPump{
      +string communication
      +read_version()
      +read_force()
      +write_force()
      +write_run_infuse()
      +write_run_withdraw()
      +write_infuse_rate()
      +write_withdraw_rate()
      +write_infuse_ramp()
      +write_withdraw_ramp()
    }

    Equipment <|-- SyringePump 
    SyringePump <|-- HarvardPump
    Equipment *-- Rabbit
    Equipment *-- State
    SyringePump *-- Syringe


    class Light {
        + write_on()
        + write_off()
    }

    class PicoLight {
        + string color
        + string communication
        + int pin
        + int frequency
        + int power
        + read_color()
        + read_pin()
        + write_pin()
        + read_frequency()
        + write_frequency()
        + read_power()
        + write_power()
    }

    Equipment <|-- Light 
    Light <|-- PicoLight

```