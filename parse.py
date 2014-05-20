# import struct
from struct import unpack
from StringIO import StringIO
import math

# This example demonstrates how to read a binary file, by reading the width and
# height information from a bitmap file. First, the bytes are read, and then
# they are converted to integers.

# When reading a binary file, always add a 'b' to the file open mode
with open('udetails.oab', 'rb') as f:
    (ulVersion, ulSerial, ulTotRecs) = unpack('<III', f.read(4 * 3))
    assert ulVersion == 32, 'This only supports OAB Version 4 Details File'
    print "Total Record Count: ", ulTotRecs

    # OAB_META_DATA
    cbSize = unpack('<I', f.read(4))[0]

    # print "OAB_META_DATA",
    meta = StringIO(f.read(cbSize - 4))

    # rgHdrcAtts = unpack('<I', meta[0:4])[0]

    HDR_cAtts = unpack('<I', meta.read(4))[0]
    print "rgHdrAtt HDR_cAtts",HDR_cAtts
    for rgProp in range(HDR_cAtts):
      ulPropID = unpack('<I', meta.read(4))[0]
      ulFlags  = unpack('<I', meta.read(4))[0]
      print rgProp, ulPropID, ulFlags

    OAB_cAtts = unpack('<I', meta.read(4))[0]
    print "rgOabAtts OAB_cAtts", OAB_cAtts
    for rgProp in range(OAB_cAtts):
      ulPropID = unpack('<I', meta.read(4))[0]
      ulFlags  = unpack('<I', meta.read(4))[0]
      print rgProp, ulPropID, ulFlags

    # OAB_V4_REC (Header Properties)
    cbSize = unpack('<I', f.read(4))[0]
    # print "OAB_V4_REC",
    f.read(cbSize - 4)


    while True:
      read = f.read(4)
      if read == '':
        break

      cbSize = unpack('<I', read)[0]

      chunk = StringIO(f.read(cbSize - 4))

      presenceBitArray = bytearray(chunk.read(int(math.ceil(OAB_cAtts / 8.0))))

      print [(presenceBitArray[i / 8] >> (i % 8)) & 1 for i in range(OAB_cAtts)]


      # print presenceBitArray
