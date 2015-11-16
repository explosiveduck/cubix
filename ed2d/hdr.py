import math
import struct
import re
from operator import itemgetter
from ed2d import files

def convertComponent(expo, val):
    v = val / 256.0
    d = math.pow(2, expo)
    return v * d

def getValueFromStream(FILE):
    return ord(FILE.read(1))

class HDR(object):
    def __init__(self):
        self.width = -1
        self.height = -1
        self.cols = []

class HDRLoader(object):
    def __init__(self):
        self.R = 0
        self.G = 1
        self.B = 2
        self.E = 3

        # Mininum scanline length for encoding
        self.MINELEN = 8
        # Maximum scanline length for encoding
        self.MAXELEN = 0x7fff

        self.RGBE = [-1, -1, -1, -1]

        # Store the scanline stuff here
        self.scanline = None

    def workOnRGBE(self, hdrFILE, length):
        scanIndex = 0
        while length > 0:
            expo = self.scanline[scanIndex][self.E] - 128
            hdrFILE.cols.append(convertComponent(expo, self.scanline[scanIndex][self.R]))
            hdrFILE.cols.append(convertComponent(expo, self.scanline[scanIndex][self.G]))
            hdrFILE.cols.append(convertComponent(expo, self.scanline[scanIndex][self.B]))
            scanIndex = scanIndex + 1
            length = length - 1


    def deCrunch(self, length, FILE):
        
        if length < self.MINELEN or length > self.MAXELEN:
            return oldDeCrunch(length, FILE)

        i = getValueFromStream(FILE)
        if i is not 2:
            # stuff about file parsing c style
            return self.oldDeCrunch(length, FILE)

        scanIndex = 0

        self.scanline[scanIndex][self.G] = getValueFromStream(FILE)
        self.scanline[scanIndex][self.B] = getValueFromStream(FILE)

        i = getValueFromStream(FILE)

        if self.scanline[scanIndex][self.G] is not 2 or self.scanline[scanIndex][self.B] & 128:
            self.scanline[scanIndex][self.R] = 2
            self.scanline[scanIndex][self.E] = i
            return self.oldDeCrunch(length - 1, FILE)

        # Read each component
        for i in range(4):
            for j in range(length - 1):
                code = getValueFromStream(FILE)
                # Run
                if code > 128:
                    code &= 127
                    val = getValueFromStream(FILE)
                    while code:
                        self.scanline[j + 1][i] = val
                        code -= 1
                # Non-Run
                else:
                    while code:
                        self.scanline[j + 1][i] = getValueFromStream(FILE)
                        code -= 1

        if getValueFromStream(FILE) is None:
            return False

    def oldDeCrunch(self,length, FILE):
        scanIndex = 0
        rshift = 0

        while length > 0:
            self.scanline[scanIndex][self.R] = getValueFromStream(FILE)
            self.scanline[scanIndex][self.G] = getValueFromStream(FILE)
            self.scanline[scanIndex][self.B] = getValueFromStream(FILE)
            self.scanline[scanIndex][self.E] = getValueFromStream(FILE)

            if (getValueFromStream(FILE) is None):
                return False

            if (self.scanline[scanIndex][self.R] is 1 and self.scanline[scanIndex][self.G] is 1 and self.scanline[scanIndex][self.B] is 1):
                for i in range(self.scanline[scanIndex][self.E] << rshift, 0, -1):
                    self.scanline[scanIndex][0] = self.scanline[scanIndex - 1][0]
                    scanIndex = scanIndex + 1
                    length = length - 1
                rshift += 8
            else:
                scanIndex = scanIndex + 1
                length = length - 1
                rshift = 0
            return True

    def load(self, fileName, hdrf):
        filePath = files.resolve_path('data', 'images', fileName)
        f = open(filePath, 'rb')

        strf = ''.join(struct.unpack('10s', f.read(10)))
        if strf != '#?RADIANCE':
            f.close()
            return False

        f.seek(1)

        cmd = []
        c = 0
        oldc = 0
        while True:
            oldc = c
            c = ord(f.read(1))
            if c is 0xa and oldc is 0xa:
                break
            cmd.append(c)

        reso = []
        while True:
            c = ord(f.read(1))
            cstr = str(unichr(c))
            reso.append(cstr)
            if c == 0xa:
                break

        resoStr = "".join(reso)
        resoStrUnformat = re.match('\-Y (?P<_0>\d+) \+X (?P<_1>\d+)', resoStr)
        (ws, hs) = map(itemgetter(1), sorted(resoStrUnformat.groupdict().items()))

        w = int(ws)
        h = int(hs)

        hdrf.width = w
        hdrf.height = h

        self.scanline = [[-1 for i in range(4)] for i in range(w)]

        print("TURD", len(self.scanline))

        if not self.scanline:
            print("File closed because scanline not found.")
            f.close()
            return False

        # Convert image
        for y in range(h - 1, 0, -1):
            # If self.scanline doesn't update is because of this
            if (self.deCrunch(w, f) is False):
                break
            # This should update the cols array in hdrf which is the HDR Class.
            # If hdrf.cols doesn't update is because of this
            self.workOnRGBE(hdrf, w)

        f.close()


myhdrtest = HDR()
myhdrtestloader = HDRLoader()
myhdrtestloader.load("grace_probe.hdr", myhdrtest)

shit = [0.0 for i in range(1000 * 1000 * 3)]
print("FUCK", len(shit))
print("HDR File Info")
print(myhdrtest.width, myhdrtest.height)
print("Size of the image: ", len(myhdrtest.cols))



