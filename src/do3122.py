#!/bin/python

import logging
import serial
import json
import os

digitDict = {
  0x5f:'0',
  0x06:'1',
  0x6b:'2',
  0x2f:'3',
  0x36:'4',
  0x3d:'5',
  0x7d:'6',
  0x07:'7',
  0x7f:'8',
  0x3f:'9'
}



with open('config.json') as js_conf:
  config = json.load(js_conf)

if not os.path.exists(config['outdir']):
  os.makedirs(config['outdir'])


def sync(ser : serial) -> bytearray:

  rxSync = b''

  while bytearray([0xAA,0x55,0x52,0x24]) not in rxSync:
    rxSync += ser.read()

  rxSync += ser.read(18)

  logger.debug('sync')

  return rxSync[-22:]


def processPacket(data : bytearray):

  global currentA
  global config

  multiplier = 1.0

  if data[21] & 0xCC == 0x04:
    outfile = 'current'
  elif data[21] & 0xCC == 0x08:
    outfile = 'voltage'
  elif data[21] & 0xCC == 0x40:
    outfile = 'resistance'
  elif data[21] & 0xCC == 0x80:
    outfile = 'frequency'
  elif data[20] == 0x01:
    outfile = 'temperature_c'
  elif data[20] == 0x02:
    outfile = 'temperature_f'
  elif data[20] == 0x90:
    outfile = 'capacitance_f'
    multiplier = 0.001
  elif data[20] == 0xA0:
    outfile = 'capacitance_f'
    multiplier = 0.000001
  elif data[20] == 0xC0:
    outfile = 'capacitance_f'
    multiplier = 0.000000001
  else:
    return

  if data[10] & 0x07 == 0x02:
    outfile += '_ac'
  elif data[10] & 0x07 == 0x04:
    outfile += '_dc'
  elif data[10] & 0x07 == 0x01:
    # Diode test
    return

  if data[21] & 0x33 == 0x01:
    multiplier = 0.000001
  elif data[21] & 0x33 == 0x02:
    multiplier = 0.001
  elif data[21] & 0x33 == 0x10:
    multiplier = 1000000
  elif data[21] & 0x33 == 0x20:
    multiplier = 1000

  if data[10] & 0x08 != 0:
    valuestr = '-'
  else:
    valuestr = ''

  for x in data[9:5:-1]:
    if x & 0x80:
      valuestr += '.'

    if x == 0:
      continue

    valuestr += digitDict[x & 0x7f]

  result = float(valuestr) * multiplier  

  with open(os.path.join(config['outdir'], outfile),'w') as f:
    f.write(str(result))

  logger.debug('{0} : {1}'.format(outfile,result))


def main():

  rxData = b''

  with serial.Serial(config['dmmport'], 9600, timeout=5) as ser:

    rxData = sync(ser)

    while True:

      debugstr = 'rx - '

      for x in rxData:
        debugstr += '{:02X} '.format(x)

      logger.debug(debugstr)

      if len(rxData) != 22 or rxData[0] != 0xAA or rxData[1] != 0x55 or rxData[2] != 0x52 or rxData[3] != 0x24:
        rxData = sync(ser)

      try:
        processPacket(rxData)
      except:
        logger.exception('Oh no!')

      rxData = ser.read(22)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info('Started DO3122 logger!')


main()
