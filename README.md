# homeassistant-paxcalima
Home assistant Custom component for  Pax Calima fan

This is offered AS IS. Feel free to fork. 
Developed and tested in HA version 0.108.9. 

## Installation

1. First install pycalima
```
#Get the latest to your work directory 
wget https://github.com/PatrickE94/pycalima/archive/master.zip
unzip master.zip
cd pycalima-master

#Install as python package
# cmdline.py is in wrong directory, move it
mv cmdline.py pycalima
pip3 install . 
# README.rst mentions run.py but this version does not have it. Check it from other forks

# now calima cmdline works
calima -h
```

1. Find out the MAC address and pin of your Pax Calima with calima -s. Pin code is in you fans motor unit. 
1. Put __init__.py, sensor.py, manifest.json into <config>/custom_components/paxcalima/ on your home assistant installation (where <config> is the directory where your config file resides).
1. Add the following to your configuration.yaml (or modify your sensor heading, if you already have one):

```yaml
sensor:
  - platform: paxcalima
    mac: 00:11:22:AA:BB:CC # replace with MAC of your Pax Calima 
    pin: 57854677 # Replace with you pin code
    name: Projector Room(optional)
```

Then restart Home Assistant and if everything works, you'll have some new sensors.
