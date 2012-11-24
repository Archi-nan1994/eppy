"""idd comments have gaps in them.
With \note fields as indicated
This code fills those gaps
see: SCHEDULE:DAY:LIST as an example"""

import sys
from pprint import pprint
sys.path.append('../EPlusInputcode')
from EPlusCode.EPlusInterfaceFunctions import readidf

def intinlist(lst):
    """test if int in list"""
    for item in lst:
        try:
            item = int(item)
            return True
        except ValueError, e:
            pass
    return False
    
def replaceint(fname, replacewith='%s'):
    """replace int in lst"""
    words = fname.split()
    for i, word in enumerate(words):
        try:
            word = int(word)
            words[i] = '%s'
        except ValueError, e:
            pass
    return ' '.join(words)

# read code
iddfile = "../iddfiles/Energy+V6_0.idd"
fname = "./walls.idf" # small file with only surfaces
data, commdct = readidf.readdatacommdct(fname, iddfile=iddfile)

dt = data.dt
dtls = data.dtls
gkeys = [dtls[i] for i in range(len(dtls)) if commdct[i].count({}) > 2]
# gkey = keys that have comment gaps
for key_txt in gkeys:
    # key_txt = 'SCHEDULE:YEAR'
    if key_txt in ['MATERIALPROPERTY:GLAZINGSPECTRALDATA', 
                    'GROUNDHEATTRANSFER:SLAB:XFACE',
                    'GROUNDHEATTRANSFER:SLAB:YFACE',
                    'GROUNDHEATTRANSFER:SLAB:ZFACE',
                    'GROUNDHEATTRANSFER:BASEMENT:XFACE',
                    'GROUNDHEATTRANSFER:BASEMENT:YFACE',
                    'GROUNDHEATTRANSFER:BASEMENT:ZFACE',
                    'TABLE:ONEINDEPENDENTVARIABLE',
                    'TABLE:TWOINDEPENDENTVARIABLES',
                    'TABLE:MULTIVARIABLELOOKUP']: # the gaps are hard to fill 
                                                # here. May not be necessary,
                                                # as these may not be used.
        continue
    print key_txt
    key_i = dtls.index(key_txt.upper())
    comm = commdct[key_i]



    # get all fields
    fields = []
    for field in comm:
        if field.has_key('field'):
            fields.append(field)

    # get repeating field names
    fnames = [field['field'][0] for field in fields]
    fnames = [fname for fname in fnames if intinlist(fname.split())]
    fnames = [(replaceint(fname), None) for fname in fnames]
    dct = dict(fnames)
    repnames = fnames[:len(dct.keys())]
    first = repnames[0][0] % (1, )

    # get all comments of the first repeating field names
    firstnames = [repname[0] % (1, ) for repname in repnames]
    fcomments = [field for field in fields if field['field'][0] in firstnames]
    fcomments = [dict(fcomment) for fcomment in fcomments]
    for cm in fcomments:
        fld = cm['field'][0]
        fld = replaceint(fld)
        cm['field'] = [fld]

    for i, cm in enumerate(comm[1:]):
        if cm['field'][0] == first:
            break
    first_i = i + 1

    newfields = []
    for i in range(1, len(comm[first_i:]) / len(repnames) + 1):
        for fcomment in fcomments:
            nfcomment = dict(fcomment)
            fld = nfcomment['field'][0]
            fld = fld % (i, )
            nfcomment['field'] = [fld]
            newfields.append(nfcomment)

    for i, cm in enumerate(comm):
        if i < first_i:
            continue
        else:
            afield = newfields.pop(0)
            comm[i] = afield
     
    # for i in range(10):
    #     pprint(comm[:2])