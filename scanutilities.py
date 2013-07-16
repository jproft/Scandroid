# scanutilities.py 1.5
#
# the Scandroid
# Copyright (C) 2005 Charles Hartman
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the 
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version. See the accompanying file, gpl.txt, for full
# details.
# OSI Certified Open Source Software
#
# This module contains utility classes and out-of-class functions.

# This data class will eventually replace the free-floating structure in
# scanfuncs.py. It will probably have a few get/set methods to streamline
# the code that uses it. So far, it's doing nothing.
class LineData:
    def __init__(self):
        self.linetext = ''
        self.lfeet = 5
        self.lfeetset = False
        self.footlist = []
        self.lastfoot = ''
        self.hremain = (0, 0)
        self.midremain = (0, 0)
        self.promcands = []


## our handy helpers from the ActiveState Cookbook site!

def getPermutations(a):		# Shalabh Chaturvedi, AS Cookbook
    if len(a) == 1 or len(a) > 9: yield a
    else:
        for i in range(len(a)):
            this = a[i]
            rest = a[:i] + a[i+1:]
            for p in getPermutations(rest): yield this + p

def uniquePermutations(lst):
    slist = []
    for s in getPermutations(lst): slist.append(s)
    u = {}					# this common trick got from Tim Peters, ASC
    for s in slist: u[s] = 1
    retlist = u.keys()
    retlist.sort()
    return retlist

def dictinvert(d):			# Jason Drew from AS Cookbook
    inv = {}
    for k, v in d.iteritems():
        keys = inv.setdefault(v, [])
        keys.append(k)
    return inv

def footfinder(fDict, scansion, chunksize, startpoint, endpoint):
    """Generator to return a next foot name,
    updating index within (part of) scanline.

    If endpoint not given, set to end of scansion string. Indices figured and
    yielded are within that string; if it's offset from the beginning of the
    actual line, caller is responsible for adding that offset. This makes it 
    useful both for start-of-line fragments (and whole lines) and for
    middles of lines.
    """
    while startpoint < endpoint:
        possfoot = scansion[startpoint:startpoint+chunksize]
        if fDict.has_key(possfoot):
            startpoint += chunksize
            yield fDict[possfoot], startpoint
        else: yield '', startpoint

def longestMatch(rx, s):			# code by Kent Johnson from python-list
    """Find the longest match for regular expression rx in string s.
    
    This nice, simple function replaces some wonderful, baroque, untunable
    one-line magic I was trying to refine . . .
    
    Returns (start, length) for the match or (None, None) if no match found.
    Condition that sets length can prefer either first or last "longest";
    adopting the latter for now on the general principle that lines tend to be
    more regular at their ends than at their beginnings (how general is this?),
    and on the ground that my RE step methods handle the pre-regular head of a
    line slightly better than the post-regular tail.
    """
    start = length = current = 0
    while True:
        m = rx.search(s, current)
        if not m: break
        mStart, mEnd = m.span()
        current = mStart + 1
        # it is not at all clear which of these is more generally correct!
        # adopting the latter on rough principle
        # that lines' ends are more regular (?)
        #if (mEnd - mStart) > length:		# returns FIRST longest
        if (mEnd - mStart) >= length:	# returns LAST longest
            start = mStart
            length = mEnd - mStart
    if length: return start, length
    return None, None


def AltLineLenCalc(lexmarks):
    """Figure line-length in feet by counting non-adjacent stresses.
    
    This is not reliable in itself, but it's good at establishing a 
    minimum number of feet. It helps little with iambics, but more
    with some anapestics. So at present it's used in scanAnapestics,
    in a max() along with the other way of calculating length.
    
    Specialization: The elimination of a stress at the beginning of the line 
    works well with anapestics, but would not work at all with iambics.
    """
    marklist = list(lexmarks)
    for inx, m in enumerate(marklist):
        if inx == 0 or marklist[inx-1] == '/':
            marklist[inx] = 'x'
    return marklist.count('/')
