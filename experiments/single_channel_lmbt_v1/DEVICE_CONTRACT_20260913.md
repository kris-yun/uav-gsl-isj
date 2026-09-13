# FKT-AQI-L device contract for the single-channel route

## Evidence source

Vendor technical-contact answers supplied by the user on 2026-09-13.
The source screenshot is not copied into the repository; its SHA-256 is
`646f3a9c34e379c141a6e3c5738cccde38775a6b4157b1383d80044befc7261b`.

## Confirmed answers

1. The purchased device is diffusion sampling, not pump sampling.
2. Data are uploaded once per second.
3. GPS uploads longitude and latitude only. The SD/local history preserves the
   data points uploaded to the cloud rather than a faster hidden raw stream.
4. The exported VOC field is described by the vendor as the original VOC
   concentration.

## Frozen implementation interpretation

- The deployable gas input is one VOC concentration value per second.
- Do not assume a 5 Hz gas stream or recover sub-second samples from the SD card.
- Altitude and higher-rate pose must come from the UAV flight controller.
- Associate each 1 Hz gas report with the buffered UAV pose at the same time;
  interpolate the UAV pose rather than duplicating one gas value across several
  poses.
- Treat the exported value as the device's concentration output. The answer does
  not establish access to ADC current, PID electrode signal, or pre-calibration
  electronics.
- The device has no controllable intake actuator. Coded Receptor Intervention
  is outside the current hardware contract and must not be simulated or claimed
  as the deployable main mechanism.
- A sample packet is not required for theory or offline premise tests. It is
  required only when implementing the final live-device adapter.

## Remaining non-blocking interface item

At live integration, obtain any one of: a sample device packet, a sample export,
or the vendor data dictionary. Use it only to map field names, units, timestamp,
and transport framing into the frozen one-second VOC contract.
