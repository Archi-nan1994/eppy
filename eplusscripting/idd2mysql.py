"""experiment with moving idd to a mysql db"""

import sys
sys.path.append('../EPlusInputcode')
from EPlusCode.EPlusInterfaceFunctions import readidf

# read code
iddfile = "../iddfiles/Energy+V6_0.idd"
fname = "./walls.idf" # small file with only surfaces
data, commdct = readidf.readdatacommdct(fname, iddfile=iddfile)

dt = data.dt
dtls = data.dtls
dct = {}
for i in range(len(dtls)):
    comm = commdct[i]
    for item in comm:
        for key in item.keys():
            key = key.upper()
            if not key.startswith('EXTENSIBLE'):
                dct[key.upper()] = None

for key in dct.keys():
    print key
            