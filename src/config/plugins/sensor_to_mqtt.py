# Set True here to enable this plug-in
enabled = False

# Address of MQTT broker
server = 'Please fill in'

# Port where MQTT broker is listening
port = 8883

# Username to login to MQTT broker
user = 'Please fill in'

# Password to login to MQTT broker
password = 'Please fill in'

# Say if SSL/TLS encryption will be used to communicate with MQTT broker
ssl = True

# Topic to be used to present sensor on MQTT
topic = 'vindriktning/sensor1'

# Period how often the data shall be refreshed on MQTT
period = 180

# Time after which system retry to connect to MQTT in the case of failure
retry_time = 60
