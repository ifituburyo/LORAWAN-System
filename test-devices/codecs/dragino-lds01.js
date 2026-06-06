// Dragino LDS01 — Door open/close sensor
// Reference: https://www.dragino.com/products/lora-lorawan-end-node/item/171-lds01.html

function decodeUplink(input) {
  var bytes = input.bytes;
  var data = {};

  // Battery (mV)
  data.BatV = ((bytes[0] << 8) | bytes[1]) / 1000;

  // Mode + door status
  var mode = bytes[2] & 0xC0;
  var doorOpen = (bytes[2] & 0x80) ? true : false;
  var waterLeak = (bytes[2] & 0x40) ? true : false;

  data.MOD = mode >> 6;
  data.DOOR_OPEN_STATUS = doorOpen ? "OPEN" : "CLOSED";
  data.WATER_LEAK_STATUS = waterLeak ? "LEAK" : "DRY";

  // Open/close event counter
  data.DOOR_OPEN_TIMES = (bytes[3] << 16) | (bytes[4] << 8) | bytes[5];

  // Last door-open duration in minutes
  data.LAST_DOOR_OPEN_DURATION_MIN = (bytes[6] << 16) | (bytes[7] << 8) | bytes[8];

  return {
    data: data,
    warnings: [],
    errors: []
  };
}
