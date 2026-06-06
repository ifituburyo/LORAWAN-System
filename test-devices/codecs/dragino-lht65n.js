// Dragino LHT65N — Temperature + Humidity sensor
// Paste this entire file into ChirpStack Device Profile → Codec → Encode/Decode
// Reference: https://www.dragino.com/downloads/index.php?dir=LHT65/

function decodeUplink(input) {
  var bytes = input.bytes;
  var value;
  var data = {};

  // Battery
  value = (bytes[0] << 8) | bytes[1];
  data.BatV = (value & 0x3FFF) / 1000;

  // Built-in temperature (SHT20/SHT31)
  value = (bytes[2] << 8) | bytes[3];
  if (bytes[2] & 0x80) {
    value |= 0xFFFF0000;
  }
  data.TempC_SHT = (value / 100).toFixed(2);

  // Built-in humidity
  value = (bytes[4] << 8) | bytes[5];
  data.Hum_SHT = (value / 10).toFixed(1);

  // External sensor type
  var extSensor = bytes[6];
  switch (extSensor) {
    case 0x01:
      data.Ext_sensor = "Temperature Sensor";
      value = (bytes[7] << 8) | bytes[8];
      if (bytes[7] & 0x80) value |= 0xFFFF0000;
      data.TempC_DS = (value / 100).toFixed(2);
      break;
    case 0x09:
      data.Ext_sensor = "Counting Sensor";
      data.Count = (bytes[7] << 24) | (bytes[8] << 16) | (bytes[9] << 8) | bytes[10];
      break;
    default:
      data.Ext_sensor = "Unknown (" + extSensor + ")";
  }

  return {
    data: data,
    warnings: [],
    errors: []
  };
}

function encodeDownlink(input) {
  // LHT65N supports downlinks for config (interval, etc.) — see Dragino docs
  return {
    bytes: [],
    fPort: 1,
    warnings: [],
    errors: []
  };
}
