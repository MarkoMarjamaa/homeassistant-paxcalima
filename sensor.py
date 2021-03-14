import logging
import struct
import datetime
import subprocess

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.const import (TEMP_CELSIUS, DEVICE_CLASS_HUMIDITY, DEVICE_CLASS_TEMPERATURE, DEVICE_CLASS_PRESSURE, STATE_UNKNOWN)

from pycalima.Calima import Calima

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'paxcalima'
CONF_MAC = 'mac'
CONF_PIN = 'pin'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Required(CONF_PIN): cv.string,
})

MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(minutes=15)
SENSOR_TYPES = [
    ['humidity', 'Humidity', '%', None, DEVICE_CLASS_HUMIDITY],
    ['temperature', 'Temperature', TEMP_CELSIUS, None, DEVICE_CLASS_TEMPERATURE],
    ['light', 'Light', 'lux', None, None],
    ['rpm', 'RPM', 'rpm', None, None],
    ['mode', 'Mode', None, None, None],
    ['boostmode', 'BoostMode', None, None, None],
    ['boostmodespeed', 'BoostMode Speed', 'rpm', None, None],
    ['boostmodesec', 'BoostMode Time', 's', None, None],
]



def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    _LOGGER.debug("Starting paxcalima")
    reader = PaxCalimaDataReader(config.get(CONF_MAC),config.get(CONF_PIN))
    add_devices([ PaxCalimaSensorEntity(reader, key,name,unit,icon,device_class) for [key, name, unit, icon, device_class] in SENSOR_TYPES])

class PaxCalimaDataReader:
    def __init__(self, mac, pin):
        self._mac = mac
        self._pin = pin
        self._state = { }

    def get_data(self, key):
        if key in self._state:
            return self._state[key]
        return STATE_UNKNOWN

    @property
    def mac(self):
        return self._mac

    @property
    def pin(self):
        return self._pin

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        _LOGGER.debug("Pax Calima updating data")
        fan = None
        
        try:
    
            # Connect to device
            _LOGGER.debug('Connecting')
            fan = Calima(self._mac, self._pin)
            
            if (fan is None):
                _LOGGER.debug('Not connected')
            else:
                _LOGGER.debug('Reading data')
                FanState = fan.getState()
                BoostMode = fan.getBoostMode()
				
                if (FanState is None):
                    _LOGGER.debug('Could not read data')
                else: 
                    self._state['humidity'] = FanState.Humidity
                    self._state['temperature'] = FanState.Temp
                    self._state['light'] = FanState.Light
                    self._state['rpm'] = FanState.RPM
                    self._state['mode'] = FanState.Mode

                    self._state['boostmode'] = BoostMode.OnOff
                    self._state['boostmodespeed'] = BoostMode.Speed
                    self._state['boostmodesec'] = BoostMode.Seconds
        except :
            _LOGGER.debug('Not connected, error')

        finally:
            if fan is not None:
                _LOGGER.debug('Disconnecting')
                fan.disconnect()
 
class PaxCalimaSensorEntity(Entity):
    """Representation of a Sensor."""

    def __init__(self, reader, key, name, unit, icon, device_class):
        """Initialize the sensor."""
        self._reader = reader
        self._key = key
        self._name = name
        self._unit = unit
        self._icon = icon
        self._device_class = device_class

    @property
    def name(self):
        """Return the name of the sensor."""
        return 'Pax Calima {}'.format(self._name)

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def device_class(self):
        """Return the icon of the sensor."""
        return self._device_class

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._reader.get_data(self._key)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def unique_id(self):
        return '{}-{}'.format(self._reader.mac, self._name)

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self._reader.update()
