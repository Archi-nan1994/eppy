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

"""read the html outputs"""


import string
import collections
from bs4 import BeautifulSoup, NavigableString, Tag

class NotSimpleTable(Exception):
    pass
        

def is_simpletable(table):
    """test if the table has only strings in the cells"""
    tds = table('td')
    for td in tds:
        if td.contents != []:
            if len(td.contents) == 1:
                if not isinstance(td.contents[0], NavigableString):
                    return False
            else:
                return False
    return True

def table2matrix(table):
    """convert a table to a list of lists - a 2D matrix"""

    if not is_simpletable(table):
        raise NotSimpleTable, "Not able read a cell in the table as a string"
    rows = []
    for tr in table('tr'):
        row = []
        for td in tr('td'):
            try:
                row.append(td.contents[0])
            except IndexError, e:
                row.append('')
        rows.append(row)
    return rows

def table2val_matrix(table):
    """convert a table to a list of lists - a 2D matrix
    Converts numbers to float"""
    if not is_simpletable(table):
        raise NotSimpleTable, "Not able read a cell in the table as a string"
    rows = []
    for tr in table('tr'):
        row = []
        for td in tr('td'):
            try:
                val = td.contents[0]
            except IndexError, e:
                row.append('')
            else:
                try:
                    val = float(val)
                    row.append(val)
                except ValueError, e:
                    row.append(val)
        rows.append(row)
    return rows


def titletable(html_doc, tofloat=True):
    """return a list of [(title, table), .....]
    
    title = previous item with a <b> tag
    table = rows -> [[cell1, cell2, ..], [cell1, cell2, ..], ..]"""
    soup = BeautifulSoup(html_doc)
    btables = soup.find_all(['b', 'table']) # find all the <b> and <table> 
    titletables = []
    for i, item in enumerate(btables):
        if item.name == 'table':
            for j in range(i + 1):
                if btables[i-j].name == 'b':# step back to find a <b>
                    break
            titletables.append((btables[i-j], item))
    if tofloat:
        t2m = table2val_matrix
    else:
        t2m = table2matrix
    titlerows = [(tl.contents[0], t2m(tb)) for tl, tb in titletables]
    return titlerows
    
def _has_name(soup_obj):
    """checks if soup_obj is really a soup object or just a string
    If it has a name it is a soup object"""
    try:
        name = soup_obj.name
        if name == None:
            return False
        return True
    except AttributeError, e:
        return False    
        
def lines_table(html_doc, tofloat=True):
    """return a list of [(lines, table), .....]
    
    lines = all the significant lines before the table. 
        These are lines between this table and 
        the previous table or 'hr' tag
    table = rows -> [[cell1, cell2, ..], [cell1, cell2, ..], ..]
    
    The lines act as a description for what is in the table
    """
    soup = BeautifulSoup(html_doc)
    linestables = []
    elements = soup.p.next_elements # start after the first para
    for element in elements:
        tabletup = []
        if not _has_name(element):
            continue
        if element.name == 'table': # hit the first table
            beforetable = []
            prev_elements = element.previous_elements # walk back and get the lines
            for prev_element in prev_elements:
                if not _has_name(prev_element):
                    continue
                if prev_element.name not in ('br', None): # no lines here
                    if prev_element.name in ('table', 'hr', 'tr', 'td'): 
                        # just hit the previous table. You got all the lines
                        break
                    if prev_element.parent.name == "p":
                        # if the parent is "p", you will get it's text anyways from the parent
                        pass
                    else:
                        if prev_element.get_text(): # skip blank lines
                            beforetable.append(prev_element.get_text())
            beforetable.reverse()
            tabletup.append(beforetable)
            function_selector = {True:table2val_matrix, False:table2matrix}
            function = function_selector[tofloat]
            tabletup.append(function(element))
        if tabletup:
            linestables.append(tabletup)
    return linestables

def _asciidigits(s):
    """if s is not ascii or digit, return an '_' """
    if s not in string.ascii_letters + string.digits:
        s = '_'
    return s

def _nospace(s):
    """replace all non-ascii, non_digit or space with '_' """
    return ''.join([_asciidigits(i) for i in s])  

def _transpose(arr):
    return map(list, zip(*arr))

def report_tables(html_doc):
    """Uses the output of lines_table function to produce a set
    of report tables addressable by name """
    lines_table = readhtml.lines_table(html_doc, True)
    tableDict = {}
    for i in range(len(lines_table)):
        tableName = lines_table[i][0]
        if any("Report: " in s for s in tableName):
            reportName = [s for s in tableName if "Report: " in s]
            reportName = reportName[0]
            tableVals = lines_table[i][1]
            tableDict[reportName] = tableVals
    return tableDict

def select_table(report_name, SAMPLE_HTML):
    """Uses the output of report_tables function to produce a
        set of nested tables where table values can be
        addressed by column & row names"""
    table_dict = report_tables(SAMPLE_HTML)
    rptTable = readhtml.table_dict[report_name]
    columnHdrs = rptTable[0]
    tableContents = rptTable[1:len(columnHdrs)-1]
    rowHdrs = zip(*tableContents)[0]
    #tableData = zip(*tableContents)[1:len(tableContents[0])]

    return rowHdrs

def _make_ntgrid(grid):
    """make a named tuple grid
    
    [["",  "a b", "b c", "c d"],
     ["x y", 1,     2,     3 ],
     ["y z", 4,     5,     6 ],
     ["z z", 7,     8,     9 ],]
    will return
    ntcol(x_y=ntrow(a_b=1, b_c=2, c_d=3), 
          y_z=ntrow(a_b=4, b_c=5, c_d=6), 
          z_z=ntrow(a_b=7, b_c=8, c_d=9))"""
    hnames = [_nospace(n) for n in grid[0][1:]]
    vnames = [_nospace(row[0]) for row in grid[1:]]
    vnames_s = " ".join(vnames)
    hnames_s = " ".join(hnames)
    ntcol = collections.namedtuple('ntcol', vnames_s)
    ntrow = collections.namedtuple('ntrow', hnames_s)
    rdict = [dict(zip(hnames, row[1:])) for row in grid[1:]]  
    ntrows = [ntrow(**rdict[i]) for i, name in enumerate(vnames)]
    ntcols = ntcol(**dict(zip(vnames, ntrows)))
    return ntcols
    
def named_grid_h(grid):
    """make a horizontal named grid"""
    return _make_ntgrid(grid)
    
def named_grid_v(grid):
    """make a vertical named grid"""
    return _make_ntgrid(_transpose(grid))    