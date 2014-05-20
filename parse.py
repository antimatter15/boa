from struct import unpack
from StringIO import StringIO
import math
import binascii
from schema import PidTagSchema
import json
# this is the table of tags and codes

def hexify(PropID):
	return "{0:#0{1}x}".format(PropID, 10).upper()[2:]

def lookup(ulPropID):
	if hexify(ulPropID) in PidTagSchema:
		(PropertyName, PropertyType) = PidTagSchema[hexify(ulPropID)]
		return PropertyName
	else:
		return hex(ulPropID)

json_out = open('test.json', 'w')

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
		# print "Chunk Size: ", cbSize

		def read_str():
			# strings in the OAB format are null-terminated
			buf = ""
			while True:
				n = chunk.read(1)
				if n == "\0" or n == "":
					break
				buf += n
			return buf
			# return unicode(buf, errors="ignore")

		def read_int():
			# integers are cool aren't they
			byte_count = unpack('<B', chunk.read(1))[0]
			if 0x81 <= byte_count <= 0x84:
				byte_count = unpack('<I', (chunk.read(byte_count - 0x80) + "\0\0\0")[0:4])[0]
			else:
				assert byte_count <= 127, "byte count must be <= 127"
			return byte_count

		rec = {}

		for i in indices:
			PropID = hexify(OAB_Atts[i])
			if PropID not in PidTagSchema:
				raise "This property id (" + PropID + ") does not exist in the schema"

			(Name, Type) = PidTagSchema[PropID]

			if Type == "PtypString8" or Type == "PtypString":
				val = read_str()
				rec[Name] = val
				print Name, val
			elif Type == "PtypBoolean":
				val = unpack('<?', chunk.read(1))[0]
				rec[Name] = val
				print Name, val
			elif Type == "PtypInteger32":
				val = read_int()
				rec[Name] = val
				print Name, val
			elif Type == "PtypBinary":
				bin = chunk.read(read_int())
				rec[Name] = binascii.b2a_hex(bin)
				print Name, len(bin), binascii.b2a_hex(bin)
			elif Type == "PtypMultipleString" or Type == "PtypMultipleString8":
				byte_count = read_int()
				print Name, byte_count
				arr = []
				for i in range(byte_count):
					val = read_str()
					arr.append(val)
					print i, "\t", val
				rec[Name] = arr
	
			elif Type == "PtypMultipleInteger32":
				byte_count = read_int()
				print Name, byte_count
				arr = []
				for i in range(byte_count):
					val = read_int()
					if Name == "OfflineAddressBookTruncatedProperties":
						val = hexify(val)
						if val in PidTagSchema:
							val = PidTagSchema[val][0]
					arr.append(val)
					print i, "\t", val

				rec[Name] = arr

			elif Type == "PtypMultipleBinary":
				byte_count = read_int()
				print Name, byte_count
				arr = []
				for i in range(byte_count):
					bin_len = read_int()
					bin = chunk.read(bin_len)
					arr.append(binascii.b2a_hex(bin))
					print i, "\t", bin_len, binascii.b2a_hex(bin)
				rec[Name] = arr
			else:
				raise "Unknown property type (" + Type + ")"
				
		remains = chunk.read()
		if len(remains) > 0:
			raise "This record contains unexpected data at the end: " + remains
		
		json_out.write(json.dumps(rec) + '\n')
		
