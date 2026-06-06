// Milesight EM300-TH — Temperature + Humidity
// Reference: https://www.milesight.com/iot/product/lorawan-sensor/em300

function decodeUplink(input) {
  var bytes = input.bytes;
  var data = {};
  var i = 0;

  while (i < bytes.length) {
    var channel_id = bytes[i++];
    var channel_type = bytes[i++];

    // BATTERY
    if (channel_id === 0x01 && channel_type === 0x75) {
      data.battery = bytes[i];
      i += 1;
    }
    // TEMPERATURE
    else if (channel_id === 0x03 && channel_type === 0x67) {
      var raw = bytes[i] | (bytes[i + 1] << 8);
      if (raw & 0x8000) raw -= 0x10000;
      data.temperature = raw / 10;
      i += 2;
    }
    // HUMIDITY
    else if (channel_id === 0x04 && channel_type === 0x68) {
      data.humidity = bytes[i] / 2;
      i += 1;
    }
    else {
      break;
    }
  }

  return {
    data: data,
    warnings: [],
    errors: []
  };
}
