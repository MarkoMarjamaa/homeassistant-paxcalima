import logging
import struct
import datetime
import subprocess

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.const import (CONF_MAC, CONF_NAME, CONF_PIN, TEMP_CELSIUS, DEVICE_CLASS_HUMIDITY, DEVICE_CLASS_TEMPERATURE, DEVICE_CLASS_ILLUMINANCE, STATE_UNKNOWN)

from pycalima.Calima import Calima

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'paxcalima'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MAC): cv.string,
    vol.Required(CONF_PIN): cv.string,
    vol.Optional(CONF_NAME, default=''): cv.string,
})

MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(minutes=15)
SENSOR_TYPES = [
    ['humidity', 'Humidity', '%', None, DEVICE_CLASS_HUMIDITY],
    ['temperature', 'Temperature', TEMP_CELSIUS, None, DEVICE_CLASS_TEMPERATURE],
    ['light', 'Light', 'lx', None, DEVICE_CLASS_ILLUMINANCE],
    ['rpm', 'RPM', 'rpm', None, None],
    ['state', 'State', None, None, None],
    ['mode', 'Mode', None, None, None],
    ['fanspeed_humidity', 'Fanspeed Humidity', 'rpm', None, None],
    ['fanspeed_light', 'Fanspeed Light', 'rpm', None, None],
    ['fanspeed_trickle', 'Fanspeed Trickle', 'rpm', None, None],
    ['sensitivity_humidityon', 'Sensitivity Humidity On', None, None, None],
    ['sensitivity_humidity', 'Sensitivity Humidity', '%', None, DEVICE_CLASS_HUMIDITY],
    ['sensitivity_lighton', 'Sensitivity Light On', None, None, None],
    ['sensitivity_light', 'Sensitivity Light', 'lx', None, DEVICE_CLASS_ILLUMINANCE],
    ['lightsensorsettings_delayedstart', 'LightSensorSettings DelayedStart', 's', None, None],
    ['lightsensorsettings_runningtime', 'LightSensorSettings Runningtime', 's', None, None],
    ['heatdistributorsettings_temperaturelimit', 'HeatDistributorSettings TemperatureLimit', TEMP_CELSIUS, None, DEVICE_CLASS_TEMPERATURE],
    ['heatdistributorsettings_fanspeedbelow', 'HeatDistributorSettings FanSpeedBelow', 'rpm', None, None],
    ['heatdistributorsettings_fanspeedabove', 'HeatDistributorSettings FanSpeedAbove', 'rpm', None, None],
    ['boostmode', 'BoostMode', None, None, None],
    ['boostmodespeed', 'BoostMode Speed', 'rpm', None, None],
    ['boostmodesec', 'BoostMode Time', 's', None, None],
    ['silenthours_on', 'SilentHours On', None, None, None],
    ['silenthours_startinghour', 'SilentHours StartingHour', 'H', None, None],
    ['silenthours_startingminute', 'SilentHours StartingMinute', 'Min', None, None],
    ['silenthours_endinghour', 'SilentHours EndingHour', 'H', None, None],
    ['silenthours_endingminute', 'SilentHours EndingMinute', 'Min', None, None],
    ['trickledays_weekdays', 'TrickleDays Weekdays', None, None, None],
    ['trickledays_weekends', 'TrickleDays Weekends', None, None, None],
    ['automatic_cycles', 'Automatic Cycles', None, None, None],
]



def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
    _LOGGER.debug("Starting paxcalima")
    reader = PaxCalimaDataReader(config.get(CONF_MAC),config.get(CONF_PIN),config.get(CONF_NAME))
    add_devices([ PaxCalimaSensorEntity(reader, key,name,unit,icon,device_class) for [key, name, unit, icon, device_class] in SENSOR_TYPES])

class PaxCalimaDataReader:
    def __init__(self, mac, pin, name):
        self._mac = mac
        self._pin = pin
        self._name = name
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

    @property
    def name(self):
        return self._name

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
                FanSpeeds = fan.getFanSpeedSettings()
                Sensitivity = fan.getSensorsSensitivity()
                LightSensorSettings = fan.getLightSensorSettings()
                HeatDistributorSettings = fan.getHeatDistributor()
                BoostMode = fan.getBoostMode()
                SilentHours = fan.getSilentHours()
                TrickleDays = fan.getTrickleDays()

                if (FanState is None):
                    _LOGGER.debug('Could not read data')
                else: 
                    self._state['humidity'] = FanState.Humidity
                    self._state['temperature'] = FanState.Temp
                    self._state['light'] = FanState.Light
                    self._state['rpm'] = FanState.RPM
                    self._state['state'] = FanState.Mode

                    self._state['mode'] = fan.getMode()

                    self._state['fanspeed_humidity'] = FanSpeeds.Humidity
                    self._state['fanspeed_light'] = FanSpeeds.Light
                    self._state['fanspeed_trickle'] = FanSpeeds.Trickle

                    self._state['sensitivity_humidityon'] = Sensitivity.HumidityOn
                    self._state['sensitivity_humidity'] = Sensitivity.Humidity
                    self._state['sensitivity_lighton'] = Sensitivity.LightOn
                    self._state['sensitivity_light'] = Sensitivity.Light

                    self._state['lightsensorsettings_delayedstart'] = LightSensorSettings.DelayedStart
                    self._state['lightsensorsettings_runningtime'] = LightSensorSettings.RunningTime

                    self._state['heatdistributorsettings_temperaturelimit'] = HeatDistributorSettings.TemperatureLimit
                    self._state['heatdistributorsettings_fanspeedbelow'] = HeatDistributorSettings.FanSpeedBelow
                    self._state['heatdistributorsettings_fanspeedabove'] = HeatDistributorSettings.FanSpeedAbove

                    self._state['boostmode'] = BoostMode.OnOff
                    self._state['boostmodespeed'] = BoostMode.Speed
                    self._state['boostmodesec'] = BoostMode.Seconds

                    self._state['silenthours_on'] = SilentHours.On
                    self._state['silenthours_startinghour'] = SilentHours.StartingHour
                    self._state['silenthours_startingminute'] = SilentHours.StartingMinute
                    self._state['silenthours_endinghour'] = SilentHours.EndingHour
                    self._state['silenthours_endingminute'] = SilentHours.EndingMinute

                    self._state['trickledays_weekdays'] = TrickleDays.Weekdays
                    self._state['trickledays_weekends'] = TrickleDays.Weekends

                    self._state['automatic_cycles'] = fan.getAutomaticCycles()

 
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
        if reader.name == '':
            self._name = name
        else:
            self._name = '{} {}'.format(reader.name, name)
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
