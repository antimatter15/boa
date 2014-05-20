from struct import unpack
from StringIO import StringIO
import math
import binascii
from schema import PidTagSchema
# this is the table of tags and codes

def hexify(PropID):
  return "{0:#0{1}x}".format(PropID, 10).upper()[2:]

def lookup(ulPropID):
  if hexify(ulPropID) in PidTagSchema:
    (PropertyName, PropertyType) = PidTagSchema[hexify(ulPropID)]
    return PropertyName
  else:
    return hex(ulPropID)

# When reading a binary file, always add a 'b' to the file open mode
with open('udetails.oab', 'rb') as f:
    (ulVersion, ulSerial, ulTotRecs) = unpack('<III', f.read(4 * 3))
    assert ulVersion == 32, 'This only supports OAB Version 4 Details File'
    print "Total Record Count: ", ulTotRecs
    # OAB_META_DATA
    cbSize = unpack('<I', f.read(4))[0]
    # print "OAB_META_DATA",
    meta = StringIO(f.read(cbSize - 4))
    # the length of the header attributes
    # we don't know and don't really need to know how to parse these
    HDR_cAtts = unpack('<I', meta.read(4))[0]
    print "rgHdrAtt HDR_cAtts",HDR_cAtts
    for rgProp in range(HDR_cAtts):
      ulPropID = unpack('<I', meta.read(4))[0]
      ulFlags  = unpack('<I', meta.read(4))[0]
      # print rgProp, lookup(ulPropID), ulFlags
    # these are the attributes that we actually care about
    OAB_cAtts = unpack('<I', meta.read(4))[0]
    OAB_Atts = []
    print "rgOabAtts OAB_cAtts", OAB_cAtts
    for rgProp in range(OAB_cAtts):
      ulPropID = unpack('<I', meta.read(4))[0]
      ulFlags  = unpack('<I', meta.read(4))[0]
      # print rgProp, lookup(ulPropID), ulFlags
      OAB_Atts.append(ulPropID)
    print "Actual Count", len(OAB_Atts)
    # OAB_V4_REC (Header Properties)
    cbSize = unpack('<I', f.read(4))[0]
    f.read(cbSize - 4)

    # now for the actual stuff
    while True:
      read = f.read(4)
      if read == '':
        break
      # this is the size of the chunk, incidentally its inclusive
      cbSize = unpack('<I', read)[0]
      # so to read the rest, we subtract four
      chunk = StringIO(f.read(cbSize - 4))
      # wow such bit op
      presenceBitArray = bytearray(chunk.read(int(math.ceil(OAB_cAtts / 8.0))))
      indices = [i for i in range(OAB_cAtts) if (presenceBitArray[i / 8] >> (7 - (i % 8))) & 1 == 1]
      print "\n----------------------------------------"
      print "Chunk Size: ", cbSize

      def read_str():
        # strings in the OAB format are null-terminated
        buf = ""
        while True:
          n = chunk.read(1)
          if n == "\0" or n == "":
            break
          buf += n
        return buf

      def read_int():
        # integers are cool aren't they
        byte_count = unpack('<B', chunk.read(1))[0]
        if 0x81 <= byte_count <= 0x84:
          byte_count = unpack('<I', (chunk.read(byte_count - 0x80) + "\0\0\0")[0:4])[0]
        else:
          assert byte_count <= 127, "byte count must be <= 127"
        return byte_count

      for i in indices:
        PropID = hexify(OAB_Atts[i])
        if PropID in PidTagSchema:
          (Name, Type) = PidTagSchema[PropID]
          if Type == "PtypString8" or Type == "PtypString":
            
            print Name, Type, read_str()
          elif Type == "PtypBoolean":
            print Name, Type, unpack('<?', chunk.read(1))[0]
          elif Type == "PtypInteger32":
            print Name, Type, read_int()
          elif Type == "PtypBinary":
            bin_len = read_int()
            print Name, Type, bin_len, binascii.b2a_hex(chunk.read(bin_len))

          elif Type == "PtypMultipleString":
            byte_count = read_int()
            print Name, Type, byte_count
            for i in range(byte_count):
                print i, "\t", read_str()
      
          elif Type == "PtypMultipleInteger32":
            byte_count = read_int()
            print Name, Type, byte_count
            for i in range(byte_count):
                print i, "\t", read_int()
          elif Type == "PtypMultipleBinary":
            byte_count = read_int()
            print Name, Type, byte_count
            for i in range(byte_count):
                bin_len = read_int()
                bin = chunk.read(bin_len)
                print i, "\t", bin_len, binascii.b2a_hex(bin)

          elif Type == "PtypObject":
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print Name, Type, read_str()
          else:
            print "#########################"
            print Name, Type
        else:
          print "WALP", PropID

      remains = chunk.read()

      if len(remains) > 0:
        print "Remainder:", remains
      
