#!/bin/python

import serial


digitDict = {
  0x5f:'0',
  0x06:'1',
  0x3b:'2',
  0x2f:'3',
  0x66:'4',
  0x6d:'5',
  0x7c:'6',
  0x07:'7',
  0x7f:'8',
  0x67:'9'
}

global currentA

currentA = 0.0


def sync(ser : serial) -> bytearray:

  rxSync = b''

  while bytearray([0xAA,0x55,0x52,0x24]) not in rxSync:
    rxSync += ser.read()

  rxSync += ser.read(18)

  print(rxSync)

  return rxSync[-22:]


def processPacket(data : bytearray):

  global currentA

  if data[21] & 0x04 == 0:
    return

  if data[19] & 0x02 != 0:
    valuestr = '-'
  else:
    valuestr = ''

  for x in data[9:5:-1]:
    if x & 0x80:
      valuestr += '.'

    valuestr += digitDict[x & 0x7f]

  result = float(valuestr)  

  if data[21] & 0x02 != 0:
    valuestr += 'mA'
    result *= 0.001
  else:
    valuestr += 'A'

  print(valuestr)
  currentA = result


def main():

  rxData = b''

  with serial.Serial('/dev/dmmlink', 9600, timeout=5) as ser:

    while True:

      for x in rxData:
        print('{:X} '.format(x), end='')

      print('')

      if len(rxData) != 22 or rxData[0] != 0xAA or rxData[1] != 0x55 or rxData[2] != 0x52 or rxData[3] != 0x24:
        rxData = sync(ser)

      try:
        processPacket(rxData)
      except:
        print('???')

      rxData = ser.read(22)

main()
