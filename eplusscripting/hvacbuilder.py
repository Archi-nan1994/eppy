# Copyright (c) 2012 Santosh Philip

# This file is part of eppy.

# Eppy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Eppy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with eppy.  If not, see <http://www.gnu.org/licenses/>.

"""make plant loop snippets"""
import sys
sys.path.append('../')
import copy
import bunch_subclass
import modeleditor
from modeleditor import IDF


class SomeFields(object):
    c_fields = ['Condenser Side Inlet Node Name',
    'Condenser Side Outlet Node Name',
    'Condenser Side Branch List Name',
    'Condenser Side Connector List Name',
    'Demand Side Inlet Node Name',
    'Demand Side Outlet Node Name',
    'Condenser Demand Side Branch List Name',
    'Condenser Demand Side Connector List Name']
    p_fields = ['Plant Side Inlet Node Name',
    'Plant Side Outlet Node Name',
    'Plant Side Branch List Name',
    'Plant Side Connector List Name',
    'Demand Side Inlet Node Name',
    'Demand Side Outlet Node Name',
    'Demand Side Branch List Name',
    'Demand Side Connector List Name']

    
        
def flattencopy(lst):
    """flatten and return a copy of the list
    indefficient on large lists"""
    # modified from http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python
    TheList = copy.deepcopy(lst)
    listIsNested = True
    while listIsNested:                 #outer loop
        keepChecking = False
        Temp = []
        for element in TheList:         #inner loop
            if isinstance(element,list):
                Temp.extend(element)
                keepChecking = True
            else:
                Temp.append(element)
        listIsNested = keepChecking     #determine if outer loop exits
        TheList = Temp[:]
    return TheList

def test_flattencopy():
    """py.test for flattencopy"""
    tdata = (([1,2], [1,2]), #lst , nlst
    ([1,2,[3,4]], [1,2,3,4]), #lst , nlst
    ([1,2,[3,[4,5,6],7,8]], [1,2,3,4,5,6,7,8]), #lst , nlst
    ([1,2,[3,[4,5,[6,7],8],9]], [1,2,3,4,5,6,7,8,9]), #lst , nlst
    )
    for lst , nlst in tdata:
        result = flattencopy(lst)
        assert result == nlst
        
def makepipecomponent(idf, pname):
    """todo"""
    apipe = idf.newidfobject("Pipe:Adiabatic".upper(), pname)
    apipe.Inlet_Node_Name = "%s_inlet" % (pname, )
    apipe.Outlet_Node_Name = "%s_outlet" % (pname, )
    return apipe
    
def makepipebranch(idf ,bname):
    """make a branch with a pipe
    use standard inlet outlet names"""
    # make the pipe component first
    pname = "%s_pipe" % (bname, )
    apipe = makepipecomponent(idf, pname)
    # now make the branch with the pipe in it
    abranch = idf.newidfobject("BRANCH", bname)    
    abranch.Component_1_Object_Type = 'Pipe:Adiabatic'
    abranch.Component_1_Name = pname
    abranch.Component_1_Inlet_Node_Name = apipe.Inlet_Node_Name
    abranch.Component_1_Outlet_Node_Name = apipe.Outlet_Node_Name
    abranch.Component_1_Branch_Control_Type = "Bypass"
    return abranch
    
def makeplantloop(idf, loopname, sloop, dloop):
    """make plant loop with pip components"""

    newplantloop = idf.newidfobject("PLANTLOOP", loopname)

    fields = SomeFields.p_fields

    # for use in bunch
    flnames = [field.replace(' ', '_') for field in fields]

    # implify naming
    fields1 = [field.replace('Plant Side', 'Supply') for field in fields]
    fields1 = [field.replace('Demand Side', 'Demand') for field in fields1]
    fields1 = [field[:field.find('Name') - 1] for field in fields1]
    fields1 = [field.replace(' Node', '') for field in fields1]
    fields1 = [field.replace(' List', 's') for field in fields1]
    # changesnames to 
    # ['Supply Inlet',
    #  'Supply Outlet',
    #  'Supply Branchs',
    #  'Supply Connectors',
    #  'Demand Inlet',
    #  'Demand Outlet',
    #  'Demand Branchs',
    #  'Demand Connectors']

    # TODO : pop connectors if no parallel branches
    # make fieldnames in the plant loop
    fieldnames = ['%s %s' % (loopname, field) for field in fields1]
    for fieldname, thefield in zip(fieldnames, flnames):
        newplantloop[thefield] = fieldname
    
    # make the branch lists for this plant loop    
    sbranchlist = idf.newidfobject("BRANCHLIST",
                    newplantloop.Plant_Side_Branch_List_Name)
    dbranchlist = idf.newidfobject("BRANCHLIST",
                    newplantloop.Demand_Side_Branch_List_Name)

    # add branch names to the branchlist
    sbranchnames = flattencopy(sloop)
    # sbranchnames = sloop[1]
    for branchname in sloop[1]:
        sbranchlist.obj.append(branchname)
    dbranchnames = flattencopy(dloop)
    # dbranchnames = dloop[1]
    for branchname in dloop[1]:
        dbranchlist.obj.append(branchname)

    # make a pipe branch for all branches in the loop

    # supply side
    sbranchs = []
    for bname in sbranchnames:
        branch = makepipebranch(idf, bname)
        sbranchs.append(branch)
    # rename inlet outlet of endpoints of loop
    anode = "Component_1_Inlet_Node_Name"
    sameinnode = "Plant_Side_Inlet_Node_Name"
    sbranchs[0][anode] =  newplantloop[sameinnode]
    anode = "Component_1_Outlet_Node_Name"
    sameoutnode = "Plant_Side_Outlet_Node_Name"
    sbranchs[-1][anode] =  newplantloop[sameoutnode]
    # rename inlet outlet of endpoints of loop - rename in pipe
    pname = sbranchs[0]['Component_1_Name'] # get the pipe name
    apipe = idf.getobject('Pipe:Adiabatic'.upper(), pname) # get pipe
    apipe.Inlet_Node_Name = newplantloop[sameinnode]
    pname = sbranchs[-1]['Component_1_Name'] # get the pipe name
    apipe = idf.getobject('Pipe:Adiabatic'.upper(), pname) # get pipe
    apipe.Outlet_Node_Name = newplantloop[sameoutnode]

    # demand side
    dbranchs = []
    for bname in dbranchnames:
        branch = makepipebranch(idf, bname)
        dbranchs.append(branch)
    # rename inlet outlet of endpoints of loop - rename in branch
    anode = "Component_1_Inlet_Node_Name"
    sameinnode = "Demand_Side_Inlet_Node_Name"
    dbranchs[0][anode] =  newplantloop[sameinnode]
    anode = "Component_1_Outlet_Node_Name"
    sameoutnode = "Demand_Side_Outlet_Node_Name"
    dbranchs[-1][anode] =  newplantloop[sameoutnode]
    # rename inlet outlet of endpoints of loop - rename in pipe
    pname = dbranchs[0]['Component_1_Name'] # get the pipe name
    apipe = idf.getobject('Pipe:Adiabatic'.upper(), pname) # get pipe
    apipe.Inlet_Node_Name = newplantloop[sameinnode]
    pname = dbranchs[-1]['Component_1_Name'] # get the pipe name
    apipe = idf.getobject('Pipe:Adiabatic'.upper(), pname) # get pipe
    apipe.Outlet_Node_Name = newplantloop[sameoutnode]


    # TODO : test if there are parallel branches
    # make the connectorlist an fill fields
    sconnlist = idf.newidfobject("CONNECTORLIST",
                    newplantloop.Plant_Side_Connector_List_Name)
    sconnlist.Connector_1_Object_Type = "Connector:Splitter"
    sconnlist.Connector_1_Name = "%s_supply_splitter" % (loopname, )
    sconnlist.Connector_2_Object_Type = "Connector:Mixer"
    sconnlist.Connector_2_Name = "%s_supply_mixer" % (loopname, )
    dconnlist = idf.newidfobject("CONNECTORLIST",
                    newplantloop.Demand_Side_Connector_List_Name)
    dconnlist.Connector_1_Object_Type = "Connector:Splitter"
    dconnlist.Connector_1_Name = "%s_demand_splitter" % (loopname, )
    dconnlist.Connector_2_Object_Type = "Connector:Mixer"
    dconnlist.Connector_2_Name = "%s_demand_mixer" % (loopname, )

    # make splitters and mixers
    s_splitter = idf.newidfobject("CONNECTOR:SPLITTER", 
        sconnlist.Connector_1_Name)
    s_splitter.obj.extend([sloop[0]] + sloop[1])
    s_mixer = idf.newidfobject("CONNECTOR:MIXER", 
        sconnlist.Connector_2_Name)
    s_mixer.obj.extend([sloop[-1]] + sloop[1])
    # -
    d_splitter = idf.newidfobject("CONNECTOR:SPLITTER", 
        dconnlist.Connector_1_Name)
    d_splitter.obj.extend([dloop[0]] + dloop[1])
    d_mixer = idf.newidfobject("CONNECTOR:MIXER", 
        dconnlist.Connector_2_Name)
    d_mixer.obj.extend([dloop[-1]] + dloop[1])
    return newplantloop

def getbranchcomponents(idf, branch, utest=False):
    """get the components of the branch"""
    fobjtype = 'Component_%s_Object_Type'
    fobjname = 'Component_%s_Name'
    complist = []
    for i in xrange(1, 100000):
        try:
            objtype = branch[fobjtype % (i, )]
            if objtype.strip() == '':
                break
            objname = branch[fobjname % (i, )]
            complist.append((objtype, objname))
        except bunch_subclass.BadEPFieldError, e:
            break
    if utest:
        return complist
    else:
        return [idf.getobject(ot, on) for ot, on in complist]

def renamenodes(idf, fieldtype):
    """rename all the changed nodes"""
    renameds = []
    for key in idf.model.dtls:
        for idfobject in idf.idfobjects[key]:
            for fieldvalue in idfobject.obj:
                if type(fieldvalue) is list:
                    if fieldvalue not in renameds:
                        cpvalue = copy.copy(fieldvalue)
                        renameds.append(cpvalue)

    # do the renaming
    for key in idf.model.dtls:
        for idfobject in idf.idfobjects[key]:
            for i, fieldvalue in enumerate(idfobject.obj):
                itsidd = idfobject.objidd[i]
                if itsidd.has_key('type'):
                    if itsidd['type'][0] == fieldtype:
                        tempdct = dict(renameds)
                        if type(fieldvalue) is list:
                            fieldvalue = fieldvalue[-1]
                            idfobject.obj[i] = fieldvalue
                        else:
                            if tempdct.has_key(fieldvalue):
                                fieldvalue = tempdct[fieldvalue]
                                idfobject.obj[i] = fieldvalue
    
def getfieldnamesendswith(idfobject, endswith):
    """get the filednames for the idfobject based on endswith"""
    objls = idfobject.objls
    return [name for name in objls if name.endswith(endswith)]
    
def getnodefieldname(idfobject, endswith, fluid=''):
    """return the field name of the node
    fluid is only needed if there are air and water nodes
    fluid is Air or Water or ''. 
    if the fluid is Steam, use Water"""
    nodenames = getfieldnamesendswith(idfobject, endswith)
    fnodenames=[nd for nd in nodenames if nd.find(fluid)!=-1]
    if len(fnodenames) == 0:
        nodename = nodenames[0]
    else:
        nodename = fnodenames[0]
    return nodename
        
    
def connectcomponents(idf, components, fluid=''):
    """rename nodes so that the components get connected
    fluid is only needed if there are air and water nodes
    fluid is Air or Water or ''. 
    if the fluid is Steam, use Water"""
    for i in range(len(components) - 1):
        thiscomp = components[i]
        nextcomp = components[i + 1]
        initinletoutlet(idf, thiscomp, force=False)
        initinletoutlet(idf, nextcomp, force=False)
        betweennodename = "%s_%s_node" % (thiscomp.Name, nextcomp.Name)
        outletnodename = getnodefieldname(thiscomp, "Outlet_Node_Name", fluid)
        thiscomp[outletnodename] = [thiscomp[outletnodename], betweennodename]
        inletnodename = getnodefieldname(nextcomp, "Inlet_Node_Name", fluid)
        nextcomp[inletnodename] = [nextcomp[inletnodename], betweennodename]
    return components
     
    
def initinletoutlet(idf, idfobject, force=False):
    """initialze values for all the inlet outlet nodes for the object.
    if force == False, it willl init only if field = '' """
    def blankfield(fieldvalue):
        """test for blank field"""
        try:
            if fieldvalue.strip() == '':
                return True
            else:
                return False
        except AttributeError, e: # field may be a list
            return False
            
    inletfields = getfieldnamesendswith(idfobject, "Inlet_Node_Name")
    for inletfield in inletfields:
        if blankfield(idfobject[inletfield]) == True or force == True:
            idfobject[inletfield] = "%s_%s" % (idfobject.Name, inletfield)
    outletfields = getfieldnamesendswith(idfobject, "Outlet_Node_Name")
    for outletfield in outletfields:
        if blankfield(idfobject[outletfield]) == True or force == True:
            idfobject[outletfield] = "%s_%s" % (idfobject.Name, outletfield)
    return idfobject
    
def componentsintobranch(idf, branch, componentlist, fluid=''):
    """insert a list of components into a branch
    fluid is only needed if there are air and water nodes in same object
    fluid is Air or Water or ''. 
    if the fluid is Steam, use Water"""
    # assumes that the nodes of the component connect to each other
    # empty branch if it has existing components
    thebranchname = branch.Name
    thebranch = idf.removeextensibles('BRANCH', thebranchname) # empty the branch
    # fill in the new components with the node names into this branch
        # find the first extensible field and fill in the data in obj.
    e_index = idf.getextensibleindex('BRANCH', thebranchname)
    theobj = thebranch.obj
    modeleditor.extendlist(theobj, e_index) # just being careful here
    for comp in componentlist:
        theobj.append(comp.key)
        theobj.append(comp.Name)
        inletnodename = getnodefieldname(comp, "Inlet_Node_Name", fluid)
        theobj.append(comp[inletnodename])
        outletnodename = getnodefieldname(comp, "Outlet_Node_Name", fluid)
        theobj.append(comp[outletnodename])
        theobj.append('')
    
    return thebranch

def replacebranch(idf, loop, branch, 
                listofcomponents, fluid='', debugsave=False):
    """It will replace the components in the branch with components in 
    listofcomponents"""
    # join them into a branch
    # -----------------------
    # np1_inlet -> np1 -> np1_np2_node -> np2 -> np2_outlet
        # change the node names in the component
        # empty the old branch
        # fill in the new components with the node names into this branch

    components = listofcomponents
    connectcomponents(idf, components, fluid=fluid)
    if debugsave:
        idf.saveas("hhh3.idf")

    thebranch = branch
    componentsintobranch(idf, thebranch, components, fluid=fluid)

    # # gather all renamed nodes
    # # do the renaming
    renamenodes(idf, 'node')
    if debugsave:
        idf.saveas("hhh7.idf")

    # check for the end nodes of the loop
    if loop.key == 'PLANTLOOP':
        fields = SomeFields.p_fields
    if loop.key == 'CONDENSERLOOP':
        fields = SomeFields.c_fields
    # for use in bunch
    flnames = [field.replace(' ', '_') for field in fields]
    
    supplyconlistname = loop[flnames[3]] # Plant_Side_Connector_List_Name
    supplyconlist = idf.getobject('CONNECTORLIST', supplyconlistname)
    for i in xrange(1, 100000): # large range to hit end
        try:
            fieldname = 'Connector_%s_Object_Type' % (i, )
            ctype = supplyconlist[fieldname]
        except bunch_subclass.BadEPFieldError, e:
            break
        if ctype.strip() == '':
            break
        fieldname = 'Connector_%s_Name' % (i, )
        cname = supplyconlist[fieldname]
        connector = idf.getobject(ctype.upper(), cname)
        if connector.key == 'CONNECTOR:SPLITTER':
            firstbranchname = connector.Inlet_Branch_Name
            cbranchname = firstbranchname
            isfirst = True
        if connector.key == 'CONNECTOR:MIXER':
            lastbranchname = connector.Outlet_Branch_Name
            cbranchname = lastbranchname
            isfirst = False
        if cbranchname == thebranch.Name:
            # rename end nodes
            comps = getbranchcomponents(idf, thebranch)
            if isfirst:
                comp = comps[0]
                inletnodename = getnodefieldname(comp, 
                                        "Inlet_Node_Name", fluid)
                comp[inletnodename] = [comp[inletnodename],
                                loop[flnames[0]]] # Plant_Side_Inlet_Node_Name
            else:
                comp = comps[-1]
                outletnodename = getnodefieldname(comp, 
                                        "Outlet_Node_Name", fluid)
                comp[outletnodename] = [comp[outletnodename], 
                            loop[flnames[1]]] # .Plant_Side_Outlet_Node_Name

    demandconlistname = loop[flnames[7]] # .Demand_Side_Connector_List_Name
    demandconlist = idf.getobject('CONNECTORLIST', demandconlistname)
    for i in xrange(1, 100000): # large range to hit end
        try:
            fieldname = 'Connector_%s_Object_Type' % (i, )
            ctype = demandconlist[fieldname]
        except bunch_subclass.BadEPFieldError, e:
            break
        if ctype.strip() == '':
            break
        fieldname = 'Connector_%s_Name' % (i, )
        cname = demandconlist[fieldname]
        connector = idf.getobject(ctype.upper(), cname)
        if connector.key == 'CONNECTOR:SPLITTER':
            firstbranchname = connector.Inlet_Branch_Name
            cbranchname = firstbranchname
            isfirst = True
        if connector.key == 'CONNECTOR:MIXER':
            lastbranchname = connector.Outlet_Branch_Name 
            cbranchname = lastbranchname
            isfirst = False
        # print cbranchname, thebranch
        if cbranchname == thebranch.Name:
            # rename end nodes
            comps = getbranchcomponents(idf, thebranch)
            if isfirst:
                comp = comps[0]
                inletnodename = getnodefieldname(comp, 
                                        "Inlet_Node_Name", fluid)
                comp[inletnodename] = [comp[inletnodename],
                            loop[flnames[4]]] #.Demand_Side_Inlet_Node_Name
            if not isfirst:
                comp = comps[-1]
                outletnodename = getnodefieldname(comp, 
                                        "Outlet_Node_Name", fluid)
                comp[outletnodename] = [comp[outletnodename], 
                            loop[flnames[5]]] # .Demand_Side_Outlet_Node_Name


    if debugsave:
        idf.saveas("hhh8.idf")

    # # gather all renamed nodes
    # # do the renaming
    renamenodes(idf, 'node')
    if debugsave:
        idf.saveas("hhh9.idf")
    return thebranch



def makecondenserloop(idf, loopname, sloop, dloop):
    """make condenser loop with pipe components"""

    newcondenserloop = idf.newidfobject("CondenserLoop".upper(), loopname)

    fields = SomeFields.c_fields

    # for use in bunch
    flnames = [field.replace(' ', '_') for field in fields]

    # TODO : check if these change too.
    # simplify naming
    fields1 = [field.replace('Condenser Side', 
                                    'Cond_Supply') for field in fields]
    fields1 = [field.replace('Demand Side', 'Demand') for field in fields1]
    fields1 = [field[:field.find('Name') - 1] for field in fields1]
    fields1 = [field.replace(' Node', '') for field in fields1]
    fields1 = [field.replace(' List', 's') for field in fields1]
    # changesnames to 
    # ['Cond_Supply Inlet',
    #  'Cond_Supply Outlet',
    #  'Cond_Supply Branchs',
    #  'Cond_Supply Connectors',
    #  'Demand Inlet',
    #  'Demand Outlet',
    #  'Demand Branchs',
    #  'Demand Connectors']

    # old TODO : pop connectors if no parallel branches
    # make fieldnames in the condenser loop
    fieldnames = ['%s %s' % (loopname, field) for field in fields1]
    for fieldname, thefield in zip(fieldnames, flnames):
        newcondenserloop[thefield] = fieldname
    
    # make the branch lists for this condenser loop    
    sbranchlist = idf.newidfobject("BRANCHLIST",
                    newcondenserloop.Condenser_Side_Branch_List_Name)
    dbranchlist = idf.newidfobject("BRANCHLIST",
                    newcondenserloop.Condenser_Demand_Side_Branch_List_Name)

    # add branch names to the branchlist
    sbranchnames = flattencopy(sloop)
    # sbranchnames = sloop[1]
    for branchname in sloop[1]:
        sbranchlist.obj.append(branchname)
    dbranchnames = flattencopy(dloop)
    # dbranchnames = dloop[1]
    for branchname in dloop[1]:
        dbranchlist.obj.append(branchname)

    # make a pipe branch for all branches in the loop

    # supply side
    sbranchs = []
    for bname in sbranchnames:
        branch = makepipebranch(idf, bname)
        sbranchs.append(branch)
    # rename inlet outlet of endpoints of loop
    anode = "Component_1_Inlet_Node_Name"
    sameinnode = "Condenser_Side_Inlet_Node_Name" # TODO : change ?
    sbranchs[0][anode] =  newcondenserloop[sameinnode]
    anode = "Component_1_Outlet_Node_Name"
    sameoutnode = "Condenser_Side_Outlet_Node_Name" # TODO : change ?
    sbranchs[-1][anode] =  newcondenserloop[sameoutnode]
    # rename inlet outlet of endpoints of loop - rename in pipe
    pname = sbranchs[0]['Component_1_Name'] # get the pipe name
    apipe = idf.getobject('Pipe:Adiabatic'.upper(), pname) # get pipe
    apipe.Inlet_Node_Name = newcondenserloop[sameinnode]
    pname = sbranchs[-1]['Component_1_Name'] # get the pipe name
    apipe = idf.getobject('Pipe:Adiabatic'.upper(), pname) # get pipe
    apipe.Outlet_Node_Name = newcondenserloop[sameoutnode]

    # demand side
    dbranchs = []
    for bname in dbranchnames:
        branch = makepipebranch(idf, bname)
        dbranchs.append(branch)
    # rename inlet outlet of endpoints of loop - rename in branch
    anode = "Component_1_Inlet_Node_Name"
    sameinnode = "Demand_Side_Inlet_Node_Name" # TODO : change ?
    dbranchs[0][anode] =  newcondenserloop[sameinnode]
    anode = "Component_1_Outlet_Node_Name"
    sameoutnode = "Demand_Side_Outlet_Node_Name" # TODO : change ?
    dbranchs[-1][anode] =  newcondenserloop[sameoutnode]
    # rename inlet outlet of endpoints of loop - rename in pipe
    pname = dbranchs[0]['Component_1_Name'] # get the pipe name
    apipe = idf.getobject('Pipe:Adiabatic'.upper(), pname) # get pipe
    apipe.Inlet_Node_Name = newcondenserloop[sameinnode]
    pname = dbranchs[-1]['Component_1_Name'] # get the pipe name
    apipe = idf.getobject('Pipe:Adiabatic'.upper(), pname) # get pipe
    apipe.Outlet_Node_Name = newcondenserloop[sameoutnode]


    # TODO : test if there are parallel branches
    # make the connectorlist an fill fields
    sconnlist = idf.newidfobject("CONNECTORLIST",
                    newcondenserloop.Condenser_Side_Connector_List_Name)
    sconnlist.Connector_1_Object_Type = "Connector:Splitter"
    sconnlist.Connector_1_Name = "%s_supply_splitter" % (loopname, )
    sconnlist.Connector_2_Object_Type = "Connector:Mixer"
    sconnlist.Connector_2_Name = "%s_supply_mixer" % (loopname, )
    dconnlist = idf.newidfobject("CONNECTORLIST",
        newcondenserloop.Condenser_Demand_Side_Connector_List_Name)
    dconnlist.Connector_1_Object_Type = "Connector:Splitter"
    dconnlist.Connector_1_Name = "%s_demand_splitter" % (loopname, )
    dconnlist.Connector_2_Object_Type = "Connector:Mixer"
    dconnlist.Connector_2_Name = "%s_demand_mixer" % (loopname, )

    # make splitters and mixers
    s_splitter = idf.newidfobject("CONNECTOR:SPLITTER", 
        sconnlist.Connector_1_Name)
    s_splitter.obj.extend([sloop[0]] + sloop[1])
    s_mixer = idf.newidfobject("CONNECTOR:MIXER", 
        sconnlist.Connector_2_Name)
    s_mixer.obj.extend([sloop[-1]] + sloop[1])
    # -
    d_splitter = idf.newidfobject("CONNECTOR:SPLITTER", 
        dconnlist.Connector_1_Name)
    d_splitter.obj.extend([dloop[0]] + dloop[1])
    d_mixer = idf.newidfobject("CONNECTOR:MIXER", 
        dconnlist.Connector_2_Name)
    d_mixer.obj.extend([dloop[-1]] + dloop[1])
    return newcondenserloop

def main():
    from StringIO import StringIO
    import iddv7
    IDF.setiddname(StringIO(iddv7.iddtxt))
    idf1 = IDF(StringIO(''))
    loopname = "p_loop"
    sloop = ['sb0', ['sb1', 'sb2', 'sb3'], 'sb4']
    dloop = ['db0', ['db1', 'db2', 'db3'], 'db4']
    # makeplantloop(idf1, loopname, sloop, dloop)
    loopname = "c_loop"
    sloop = ['sb0', ['sb1', 'sb2', 'sb3'], 'sb4']
    dloop = ['db0', ['db1', 'db2', 'db3'], 'db4']
    makecondenserloop(idf1, loopname, sloop, dloop)
    idf1.saveas("hh1.idf")


if __name__ == '__main__':
    main()
