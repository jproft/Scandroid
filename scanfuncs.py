# scanfuncs.py 1.5
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
# This Scansion Machine class has the methods called by Scandroid to do the 
# actual scansion work. It owns a dictionary and instances of a Syllabizer and
# a Positioner for some of the grunt work.


import sre
import random		# second import! will be reseeded! (not a problem)
from scanstrings import *
from syllables import *
from scanpositions import *
from dictfuncs import *
from scanutilities import *

# global to this module - initialize most members for each new line in 
# ParseLine; others set by call from top level. Note: lfeet is set in several 
# places, but lfeetset is set only at top level, and consulted in this module
# only at beginning of iambic/anapestic process
lineDat = { 'linetext': '', 'lfeet': 5, 'lfeetset':False, 'footlist':[],
            'lastfoot': '', 'hremain': (0,0), 'midremain': (0,0), 'promcands':[] }
fo = open("foo.txt", "wb")

class ScansionMachine:
    
    def __init__(self):
        """Create our main helpers and compile RE patterns"""
        self.S = Syllabizer()
        self.P = Positioner()
        self.SD = ScanDict(self)
        self.vowelRE = sre.compile('[aeiouyAEIOUY]')
        self.wordBoundsRE = sre.compile(r"([-.,;:?!\(\)\"\s]+)")
        self.possIambRE = sre.compile('(x[x/])+')
        
    def SetLineFeet(self, num, setflag):
        """Frame, while deducing parameters, sets chief values here."""
        lineDat['lfeet'] = num
        lineDat['lfeetset'] = setflag

## - - - - - line-parsing code called by everybody in prep for any scansion

    def ParseLine(self, line):
        """Determine syls/stress in all words in line, store other data too.
        
        Divide the line into word-tokens (carefully!). Look up each in dictionary,
        and there or by calculation in the Syllabizer determine syllabification
        and stress. Lay all basic data-groundwork in Positioner. Return nothing.
        """
        if len(line) < 1: return None			# nothing to do
        lineDat['linetext'] = line
        lineDat['footlist'] = []
        lineDat['lastfoot'] = ''
        self.P.NewLine(len(line))					# prepare new data structures
        # Tricky: hyphens separate tokens, apostrophes don't; hyphen must go
        # first in list; double-quote needs escape; and please
        # note subtle placement of '+', which allows punct+space to be a  string
        words = self.wordBoundsRE.split(line)
        lineindex = 0		# keep track of position in list of chars
        self.dwds = []; self.cwds = []		# collections for Explainer
        for wORD in words:
            if not wORD: continue	# sre.split can produce empty returns
            # catch clitics for non-syllabic treatment, defined as:
            anyvowels = self.vowelRE.search(wORD)
            if not anyvowels:
                lineindex += len(wORD)
                continue
            # punct and whitespace to Positioner, exc. words like "'twas"
            if not wORD[0].isalpha() and (wORD[0] != '\'' or wORD == '\''):
                lineindex = self.P.AddPunct(wORD, lineindex)
                continue
            w = wORD.lower()			# for ALL internal use! e.g. in dictionary!
            syls = self._dictLookup(w)
            if syls: self.dwds.append(syls)
            else:
                syls = self.S.Syllabize(w)
                self.cwds.append(syls)
            lineindex = self.P.AddWord(syls, lineindex)	# AddWord advances index
        self.P.LocateFootDivPositions()
    
    def _dictLookup(self, word):
        """If word, or word less -s/-ed ending, is in dict, return its syls/stress.
        
        Whenever we accept something from the dictionary, we copy it, so that
        our manipulations for the sake of this line won't change the dictionary
        for others (including other instances of this line).
        """
        if word in self.SD.Dict: return self.SD.Dict[word][:]
        elif len(word) < 5: return None	# e.g., 'bed'! is 5 big/small enough?
        elif word[-1:] == 's':
            try:
                syls = self.SD.Dict[word[:-1]][:]
                if syls[-1].isupper(): syls[-1] += 'S'
                else: syls[-1] += 's'
                return syls
            except KeyError: return None
        elif word[-2:] == 'ed':
            try:
                syls = self.SD.Dict[word[:-2]][:]
                if syls[-1].isupper(): syls[-1] += 'ED'
                else: syls[-1] += 'ed'
                return syls
            except KeyError:
                try:
                    syls = self.SD.Dict[word[:-1]][:]
                    if syls[-1].isupper(): syls[-1] += 'D'
                    else: syls[-1] += 'd'
                    return syls
                except KeyError: return None
        else: return None
        
## - - - - - first visible steps of ANY scansion
    def ShowSyllables(self, logger):
        """First visible step: display anonymous mark over each syllable."""
        logger.ExpParseLine(self.dwds, self.cwds)
        return self.P.GetScanString(feet=False, punct = False, sylsOnly=True), True
            
    def ShowLexStresses(self, logger):
        """Second visible step: x and / marks replace anon. syl marks"""
        logger.ExpLexStress(self.dwds, self.cwds)
        # in case user forces choice of algorithm, which fails; see RestartNewIambicAlg
        self.lexData = self.P.charlist[:]		# now ONLY data needed to restart
        return self.P.GetScanString(False, False), True	# no feet no punct for disp

## - - - - - where iambic and anapestic steps diverge
    def ChooseAlgorithm(self, logger, deducingParams=False):
        """The "crux" step for iambics. Look ahead to see which comes out better.
        
        Choices to try are multiplied by any stress-ambiguities discovered by
        ParseLine. If neither is superior, choose at random. Announce whatever we 
        do; allow user (with menu choice) to override.
        """
        complexities = {}
        possScansions = self.P.GetAmbiguities()
        for s in possScansions:
            for algorithm in (1, 2):
                (feet, test) = self.DoAlgorithm(algorithm, s)
                complexities[(s, algorithm)] = (self._measureComplexity(feet, test), len(feet))
        lowest = min([v[0] for v in complexities.values()])
        bestkeys = [key for key in complexities if complexities[key][0] == lowest]
        ourkey = random.choice(bestkeys)
        if not deducingParams:
            self.P.AdjustMarks(ourkey[0])
            logger.ExpChooseAlg(ourkey[1], len(possScansions))
            if ourkey[1] == 1: return self.P.GetScanString(), True
            else: return self.P.GetScanString(), False
        else: return (lowest, complexities[ourkey][1])
        
## - - the quick-run-through version of iambic scansion, so as
##     to test algorithms etc. without displaying step-by-step messages
    def DoAlgorithm(self, whichAlgorithm, scansion):
        """Run through whole iambic scansion, either algorithm, silently.
        
        Called by top-level DeduceParameters to figure metron. After, if iambic,
        called by ChooseAlgorithm to try each approach. If global-to-module
        linelength not set, figure it (not reliably!) and set it for step-by-steps.
        Note that when call is from DeduceParameters, lfeetset is *false*.
        """
        ## whichAlgorithm = 1           # TESTTESTTEST
        if not lineDat['lfeetset']:
            if len(scansion) // 2 >= 2: 
                linefeet = len(scansion) // 2	# crude! but can't find reliable improvement
                lineDat['lfeet'] = linefeet		# was not set before; set for all following
            else: return ([], [])
        else: linefeet = lineDat['lfeet']
        footlist = []
        if whichAlgorithm == 1:
            normlen = linefeet * 2
            currlen = len(scansion)
            if (currlen > (normlen + 1)) and (scansion[-4:] in ('x/xx', 'xx/x')):
                lastfoot = footDict[scansion[-4:]]
                linefeet -= 1			# only in local copy!
                scansion = scansion[:-4]
            elif currlen >= normlen and scansion[-3:] in ('x/x', '//x'):
                lastfoot = footDict[scansion[-3:]]
                linefeet -= 1
                scansion = scansion[:-3]
            else: lastfoot = ''
            normlen = linefeet * 2			# unnec. if no special feet, but
            currlen = len(scansion)
            if currlen <= normlen and scansion[:4] in ('/x/x', '/xxx'):
                footlist.append('defective')
                linefeet -= 1
                scansion = scansion[1:]
            # end of special-first-last-feet section
            if currlen == normlen:				# simple disyllables
                for (footname, sylinx) in footfinder(footDict, scansion, 2, 0, len(scansion)):
                    if footname: footlist.append(footname)
                    else: return ([], [])
            elif currlen < normlen:				# defective somewhere
                candidate = scansion.find('x//')
                if candidate % 2 != 0: return ([], [])
                for (footname, sylinx) in footfinder(footDict, scansion, 2, 0, candidate):
                    if footname: footlist.append(footname)
                    else: return ([], [])
                footlist.append('defective')
                for (footname, sylinx) in footfinder(footDict, scansion, 2,
                                                     candidate+1, len(scansion)):
                    if footname: footlist.append(footname)
                    else: return ([], [])
            else:										# anapests
                need = currlen - normlen
                candidates = []
                for p in sre.finditer(r'(?=/xx/)', scansion): 
                    candidates.append(p.start() + 1)
                if len(candidates) < need:
                    for p in sre.finditer(r'(?=xx/)', scansion): candidates.append(p.start())
                i = 0
                while i < currlen:
                    if i in candidates:
                        footlist.append('anapest')
                        i += 3
                    else:
                        if footDict.has_key(scansion[i:i+2]):
                            footlist.append(footDict[scansion[i:i+2]])
                        else: return ([], [])
                        i += 2
            if lastfoot: footlist.append(lastfoot)
        else:			# algorithm 2
            (startoflongest, longest) = longestMatch(self.possIambRE, scansion)
            if startoflongest is None: return ([], [])
            if startoflongest % 2 == 0:			# divide head into disyllables
                for (footname, sylinx) in footfinder(footDict, scansion, 2, 0, startoflongest):
                    if footname: footlist.append(footname)
                    else: return ([], [])
            elif scansion[:2] == '/x':		# headless, I guess
# could use better test from alg 1: sc[:4] in ('/xxx', '/x/x'), IFF 3+ syls!!
                footlist.append('defective')
                for (footname, sylinx) in footfinder(footDict, scansion, 2, 1, startoflongest):
                    if footname: footlist.append(footname)
                    else: return ([], [])
            else:
                anap = scansion.find('xx/', 0, startoflongest)
                if anap == -1: return ([],[])
                for (footname, longest) in footfinder(footDict, scansion, 2, 0, anap):
                    if footname: footlist.append(footname)
                    else: return ([], [])
                footlist.append('anapest')
                for (footname, sylinx) in footfinder(footDict, scansion, 2, anap + 3,
                                                      startoflongest):
                    if footname: footlist.append(footname)
                    else: return ([], [])
            for (footname, sylinx) in footfinder(footDict, scansion, 2,
                                                  startoflongest, startoflongest + longest):
                if footname: footlist.append(footname)
                else: return ([], [])
            # to divide tail, check e-s endings, divide in pairs (anaps??)
            scansion = scansion[startoflongest + longest:]
            if len(scansion) > 0:
                lastfoot = ''
                if scansion[-1] == 'x' and len(scansion) > 2:
                    if footDict.has_key(scansion[-3:]):
                        lastfoot = footDict[scansion[-3:]]
                        scansion = scansion[:-3]
                for (footname, sylinx) in footfinder(footDict, scansion, 2, 0, len(scansion)):
                    if footname: footlist.append(footname)
                    else: return ([], [])
                if lastfoot: footlist.append(lastfoot)
        for inx, f in enumerate(footlist):
            if f == 'pyrrhic':
                if inx == len(footlist) - 1 or footlist[inx+1] != 'spondee':
                    f = '(iamb)'
        test = self.P.FeetAtPunctBounds(footlist)
        return (footlist, test)

    def _measureComplexity(self, footlist, boundstest):
        """Add up weighted points for each foot substituted for the iamb.
        
        The point system is highly arbitrary. It is not used to determine the basic
        foot of the line, but only to rank possibilities proposed by the caller,
        which is always DoAlgorithm. Somewhat streamlined during design of
        corresponding anapestic method.
        """
        if len(footlist) != lineDat['lfeet']: return 100	# mostly test for empty!
        feet = footlist[:]				# so we can remove parens
        points = 0
        prevIsTrochee = False
        for inx, f in enumerate(feet):
            if f[0] == '(': f = f[1:-1]	# remove parens
            # progressively stranger substitutions
            if f in ('spondee', 'pyrrhic', 'trochee'): points += 2
            if f in ('anapest', 'defective', '3rd paeon', 'amphibrach',
                           'palimbacchius', '2nd paeon'): 
                points += 4
            # (does my code even allow for this to happen??)
            if f in ('dactyl', 'cretic', 'bacchius'): points += 10
            # esepcially disruptive positional variations
            if f == 'trochee':
                if inx == len(feet) - 1: points += 6	# scazon
                if prevIsTrochee: points += 8	# "sprung rhythm"
                prevIsTrochee = True
            else: prevIsTrochee = False
            if f in ('trochee', 'defective') and not boundstest[inx]:
                    points += 4
        return points
    
## - - if one iambic algorithm fails, we try the other, starting here with a restart
    def RestartNewIambicAlg(self, logger, failedAlgorithm, scanline):
        """Reset Positioner to lexical-stress step to try other iambic algorithm.
        
        Since ChooseAlgorithm almost always prevents failures, this is called 
        almost exclusively if user forces choice to the other algorithm and it 
        fails. If both fail, ChooseAlgorithm will pick one which will also arrive 
        here, though presumably to no avail. Called only from Frame's OnStepBtn 
        function. Does not change any values in global lineDat.
        """
        #fo.write("\n",+failedAlgorithm+" - "+scanline) 
        logger.ExpRestartNewIambicAlg(failedAlgorithm, scanline)
        self.P.charlist = self.lexData[:]
        lineDat['footlist'] = []		# prevent detritus in the clean restart
        lineDat['hremain'] = (0,0)
        lineDat['midremain'] = (0,0)
        return self.P.GetScanString()

## - - - - - - - - iambic Algorithm 1: Corral the Exceptional - - - - - - - - - - - 
    def WeirdEnds(self, logger):
        """
        Parse out unusual starting and ending feet.
        We look first for end-of-line peculiarities, and then the start-of-line
        defectives, because we can't guess well about headless lines
        without knowing what the line's "normal" length is, and that's
        affected by these extra-metrical syllabic extensions at the end.
        """
        endfeet = ['x/xx', 'xx/x', 'x/x', '//x']
        marks = self.P.GetMarks()
        normlen = lineDat['lfeet'] * 2
        currlen = len(marks)
        lastfootstring = ''
        if currlen > normlen + 1 and marks[-4:] in endfeet:
            lastfootstring = marks[-4:]
        elif currlen >= normlen and marks[-3:] in endfeet:
            lastfootstring = marks[-3:]
        if lastfootstring:
            lineDat['lastfoot'] = footDict[lastfootstring]
            self.P.AddFootDivMark(len(marks) - len(lastfootstring))
        else: lineDat['lastfoot'] = ''
        # FOLLOWING IF AND LINES IN IT, BUT NOT THE ELSE, ALL CHANGED TO FIX OLD
        # BUG -- COORDINATE!
        if currlen - len(lastfootstring) <= normlen - 2 and \
                                (marks.startswith('/x/x') or marks.startswith('/xxx')):
            lineDat['footlist'].append('defective')
            self.P.AddFootDivMark(1)
            lineDat['midremain'] = (1, currlen - len(lastfootstring))
        else: lineDat['midremain'] = (0, currlen - len(lastfootstring))
        # despite the argument here, we call the Explainer for EITHER a headless
        # line or a strange last foot
        logger.ExpWeirdEnds(lineDat['lastfoot'], lineDat['footlist'])
        return self.P.GetScanString(), True
    
    def TestLengthAndDice(self, logger):
        normlen = (lineDat['lfeet'] - len(lineDat['footlist'])) * 2
        if lineDat['lastfoot']: normlen -= 2
        start = lineDat['midremain'][0]
        end = lineDat['midremain'][1]
        currlen = end - start
        logger.ExpFootDivision(currlen, normlen)
        marks = self.P.GetMarks()
        if currlen == normlen:
            for (footname, sylinx) in footfinder(footDict, marks, 2, start, end):
                if footname: lineDat['footlist'].append(footname)
                else: return self.P.GetScanString(), False
                if sylinx < end:		# not at end of line, not where lastfoot starts
                    self.P.AddFootDivMark(sylinx + lineDat['midremain'][0])
        elif currlen < normlen:
            candidate = marks.find('x//', start, end)
            if candidate % 2 != 0:			# 'x//' at odd pos hopelessly messy
                logger.Explain("\nFAIL! no good position for single-stress foot")
                return self.P.GetScanString(), False
            candidate += 2			# point directly at defective foot
            for (footname, sylinx) in footfinder(footDict, marks, 2, start, candidate):
                if footname: lineDat['footlist'].append(footname)
                else: return self.P.GetScanString(), False
                self.P.AddFootDivMark(sylinx)
            lineDat['footlist'].append('defective')
            self.P.AddFootDivMark(candidate+1)
            for (footname, sylinx) in footfinder(footDict, marks, 2, candidate+1, end):
                if footname: lineDat['footlist'].append(footname)
                else: return self.P.GetScanString(), False
                if sylinx < end: self.P.AddFootDivMark(sylinx)
        else:				# anapest(s)
            need = currlen - normlen
            candidates = [p.start()+1 for p in sre.finditer(r'(?=/xx/)', marks)]
            if len(candidates) < need:
                morecands = [p.start() for p in sre.finditer(r'(?=xx/)', marks)]
                candidates += morecands
            while start < end:
                if need and (start in candidates):
                    foot = marks[start:start+3]
                    if footDict.has_key(foot): lineDat['footlist'].append(footDict[foot])
                    else: return self.P.GetScanString(), False
                    start += 3
                    need -= 1
                else:
                    foot = marks[start:start+2]
                    if footDict.has_key(foot): lineDat['footlist'].append(footDict[foot])
                    else: return self.P.GetScanString(), False
                    start += 2
                if start < end: self.P.AddFootDivMark(start)
        if lineDat['lastfoot']: lineDat['footlist'].append(lineDat['lastfoot'])
        return self.P.GetScanString(), True
    
## - - - - - - - - iambic Algorithm 2: Maximize the Normal - - - - - - - - - - - - 
    def TryREs(self, logger):
        """Locate the longest potentially regular iambic stretch in the line.

        Here we do put a foot-div mark at the beginning or end of the line, if
        it's the beginning or end of the longest-iambics stretch, for visual
        clarity. So the follow-up, CleanUpRE, must remove any such.
        """
        marks = self.P.GetMarks()
        (startlongest, longest) = longestMatch(self.possIambRE, marks)
        if startlongest is None: return self.P.GetScanString(), False
        runend = startlongest + longest
        tail = len(marks) - runend
        self.P.AddFootDivMark(startlongest)		# even at start of line
        self.P.AddFootDivMark(runend)				# even at end of line
        lineDat['hremain'] = (0, startlongest)
        lineDat['midremain'] = (runend, len(marks))
        retstr = self.P.GetScanString(True)		# show only bounds of longest
        for (footname, sylinx) in footfinder(footDict, marks, 2, startlongest, runend):
            if footname: lineDat['footlist'].append(footname)
            else: return self.P.GetScanString(), False
            if sylinx < len(marks): 
                self.P.AddFootDivMark(sylinx)
        logger.ExpREMain(startlongest, longest, tail,
                            len(lineDat['footlist']), lineDat['lfeet'])
        return retstr, True

    def CleanUpRE(self, logger):
        """Parse beginning and end of iambic line around regular center.
        
        This is not quite as sophisticated as TestLengthAndDice above. It won't
        deal with internal defectives, or with anapests *after* the longest-iambic 
        stretch, or with 2nd-paeon endings. It could.
        """
        marks = self.P.GetMarks()
        self.P.RemoveEndFootMarks()
        head = lineDat['hremain'][1]		# know hremain[0] is 0
        tail = len(marks) - lineDat['midremain'][0]
        insertpoint = 0
        if head and (head % 2 == 0):
            for (footname, sylinx) in footfinder(footDict, marks, 2, 0, head):
                if footname: lineDat['footlist'].insert(insertpoint, footname)
                else: return self.P.GetScanString(), False
                self.P.AddFootDivMark(sylinx)
                insertpoint += 1
        elif head:
            if marks[:2] == '/x':
# option noted in DoAlg: use better test from alg 1 IFF 3+syls (/x/x, /xxx)
                lineDat['footlist'].insert(insertpoint, 'defective')
                insertpoint += 1
                for (footname, sylinx) in footfinder(footDict, marks, 2, 1, head):
                    if footname: lineDat['footlist'].insert(insertpoint, footname)
                    else: return self.P.GetScanString(), False
                    self.P.AddFootDivMark(sylinx)
                    insertpoint += 2
            else:
# NO INTERNAL DEFECTIVES! COULD SEARCH FOR 'x//', BUT DIFFICULT TO
# DECIDE BETWEEN DEF. AND ANAPEST (FIGURE FEET NEEDED? DEPENDS ON
# TAIL -- WHICH IN TURN DEPENDS ON HEAD!)
                anap = marks.find('xx/', 0, head)
                if anap == -1:
                    logger.Explain("\nFAIL! can't find needed anapest")
                    return self.P.GetScanString(), False
                else:
                    for (footname, sylinx) in footfinder(footDict, marks, 2, 0, head):
                        if footname: lineDat['footlist'].insert(insertpoint, footname)
                        else: return self.P.GetScanString(), False
                        self.P.AddFootDivMark(sylinx)
                        insertpoint += 1
                    lineDat['footlist'].append('anapest')
                    for (footname, sylinx) in footfinder(footDict, marks, 2, anap+3, head):
                        if footname: lineDat['footlist'].insert(insertpoint,footname)
                        else: return self.P.GetScanString(), False
                        self.P.AddFootDivMark(sylinx)
                        insertpoint += 1
        if tail:
            # we find x/x, //x iff tail is odd len; do NOT find 3rd paeon!
            if marks[-1] == 'x' and tail % 2 != 0:
                startlastfoot = len(marks) - 3
                if footDict.has_key(marks[-3:]): 
                    lineDat['lastfoot'] = footDict[marks[-3:]]
                    self.P.AddFootDivMark(startlastfoot)
                else: return self.P.GetScanString(), False
            else:
                startlastfoot = len(marks)
                lineDat['lastfoot'] = ''
            for (footname, sylinx) in footfinder(footDict, marks, 2,
                                                 lineDat['midremain'][0], startlastfoot):
                if footname: lineDat['footlist'].append(footname)
                else: return self.P.GetScanString(), False
                if sylinx < startlastfoot: self.P.AddFootDivMark(sylinx)
        logger.ExpRECleanUp(head, tail)
        if lineDat['lastfoot']: lineDat['footlist'].append(lineDat['lastfoot'])
        return self.P.GetScanString(), True

## - - - - - - - - end of fork between iambic Algorithms 1 & 2 - - - - - - - - - 
    def PromotePyrrhics(self, logger):
        """Identify and mark instances of promoted stress in iambic lines.^
        
        Both algorithms need this. We do it simply: find all pyrrhics and replace
        those not followed by spondee (or end of line). To handle the rare but
        prominent case of '/xxxx/', look for sequence pyrrhic followed by
        anapest, and replace with promoted anapest followed by iamb. (Not
        clear that this is always the right decision; more research is called for.)
        """
        fl = lineDat['footlist']
        if lineDat['lfeetset'] and len(fl) != lineDat['lfeet']:
            logger.Explain("\nFAIL! wrong number of feet")
            return self.P.GetScanString(), False
        d = dictinvert(footDict)
        promotions = []
        sylinx = 0
        for inx, f in enumerate(fl):
            if f == 'pyrrhic':
                if inx < len(fl) - 1 and fl[inx+1] in ('anapest', '3rd paeon'):
                    lineDat['footlist'][inx] = '(anapest)'
                    if fl[inx+1] == 'anapest':
                        lineDat['footlist'][inx+1] = 'iamb'
                    else:
                        lineDat['footlist'][inx+1] = 'amphibrach'
                    self.P.AddScanMark('%', sylinx+2)
                    self.P.EraseFootDivMark(sylinx+2)
                    self.P.AddFootDivMark(sylinx+3)
                    promotions.append(sylinx+2)
                elif inx < len(fl) - 1 and fl[inx+1] == 'trochee':
                    logger.Explain("\nFAIL! bad pyrrhic (word wrongly stressed?)")
                    return self.P.GetScanString(), False
                elif inx == len(fl) - 1 or fl[inx+1] not in ('spondee', 'palimbacchius'):
                    lineDat['footlist'][inx] = '(iamb)'
                    self.P.AddScanMark('%', sylinx+1)
                    promotions.append(sylinx+1)
            sylinx += len(d[f][0])
        logger.ExpPromotions(promotions)
        return self.P.GetScanString(), True
    
    def HowWeDoing(self, logger):
        """Report results of iambic scansion: feet, and number of sustitutions.
        
        The anlysis is crude even compared with _measureComplexity. Kiparsky 
        may suggest better possibilities, but they may not be usable without more
        intelligence about syntax than the Scandroid has or is likely to have.
        """
        substitutions = 0
        for f in lineDat['footlist']:
            if f not in ('iamb', '(iamb)'): substitutions += 1
        if lineDat['lfeetset'] and (len(lineDat['footlist']) != lineDat['lfeet']):
            logger.ExpEndGame(lineDat['footlist'], 100)	# flag of despair!
            return self.P.GetScanString(), False
        else:
            logger.ExpEndGame(lineDat['footlist'], substitutions)
            return self.P.GetScanString(), True

## - - - - - below, all code for scanning anapestics quickly and step-by-step
    def GetBestAnapLexes(self, logger, deducingParams=False):
        """Try out all stress-resolutions with calls to quick anapestic run-through.
        
        This does a main part of what ChooseAlgorithm does for iambics: get
        from the Positioner a list of alternative lexical-stress lines, each with
        a set of resolutions of stress ambiguities, and try each one out. It
        elicits a complexity measure and uses it to pick a "best."
        """
        possScansions = self.P.GetAmbiguities()
        numcands = len(possScansions)
        complexities = {}
        for p in possScansions:
            flist = self.scanAnapestics(p)
            complexities[p] = (self._anapComplexity(flist), len(flist))
        lowest = min([v[0] for v in complexities.values()])
        bestkeys = [key for key in complexities if complexities[key][0] == lowest]
        ourkey = random.choice(bestkeys)
        if not deducingParams:
            logger.ExpAnapGetBest(numcands, len(bestkeys))
            if bestkeys:
                self.P.AdjustMarks(ourkey)
                return self.P.GetScanString(), True
            else: return self.P.GetScanString(), False
        else: return (lowest, complexities[ourkey][1])
            

    def _anapComplexity(self, footlist):
        if not footlist: return 100
        points = 0
        for inx, f in enumerate(footlist):
            if f == 'bacchius': points += 2		# note: readjust
            elif f == '(anapest)': points += 1
            elif f in ('iamb', '(iamb)'): points += 2
            elif f == 'cretic': points += 4		#  can reduce!
            elif f in ('spondee', 'pyrrhic'): points += 4
            elif f in ('amphibrach', '3rd paeon'): points += 4
            elif f in ('2nd paeon', 'molossus', 'palimbacchius'):
                points += 5
        return points		
        
    def scanAnapestics(self, scansion):
        """Run through anapestic scansion silently to report success or failure.
        
        Fairly parallel to iambic DoAlgorithm. Called by DeduceParameters
        directly for quick judgment. Also called, with alternate stress-resoution
        preliminary scansions, by GetBestAnapLexes.
        """
        numsyls = len(scansion)
        if lineDat['lfeetset']: needfeet = lineDat['lfeet']
        else:
            (needfeet, excess) = divmod(numsyls, 3)
            # assume anapestic lines may be short but never long, exc. terminals
            if scansion:
                if scansion[-1] == 'x': excess -= 1	# term. slack doesn't add feet
            if excess > 0: needfeet += 1		# could be fooled by 3 disyl feet!
            altlen = AltLineLenCalc(scansion)
            needfeet = max(needfeet, altlen)
            lineDat['lfeet'] = needfeet	
        if scansion[-2:] == 'xx':		# mark promotion, treat as stressed (x% or /x%)
            scansion = scansion[:-1] + '%'
            self.P.AddScanMark('%', len(scansion)-1)
        if scansion:
            if scansion[-1] == 'x':		# see AnapSubs for special notes on last feet!
                tailstart = scansion.rfind('/')					# point to penult
                tailstart = scansion.rfind('/', 0, tailstart)	#   stress in line
                tail = numsyls - tailstart - 1
                if AnapSubs.has_key(scansion[-tail:]):
                    lastfoot = AnapSubs[scansion[-tail:]]
                else:
                    tail += 1		# desperation: one more foot to try
                    if AnapSubs.has_key(scansion[-tail:]):
                        lastfoot = AnapSubs[scansion[-tail:]]
                    else: return []                    # unknown last foot
                needfeet -= 1
                numsyls -= tail
                scansion = scansion[:-tail]
            else: lastfoot = ''
        else: lastfoot = ''
        # dividing point for anapestic steps
        if numsyls > needfeet * 3: return []		# hypermetrical??
        if numsyls == needfeet * 3:		# assign even 3s as feet
            scansion = self.AnapPromoteSlack(scansion)
            footlist = []
            for (footname, sylinx) in footfinder(AnapSubs, scansion, 3, 0, numsyls):
                if footname: footlist.append(footname)
                else: return []
        else:
            needDisyls = (needfeet * 3) - numsyls
            if needDisyls > needfeet: return []
            scansion = self.AnapPromoteSlack(scansion)
            numlist = '2' * needDisyls + '3' * (needfeet - needDisyls)
            listoflists = uniquePermutations(numlist) # CAN GO INTO INFINITE LOOP. BAD.
            for pat in listoflists:
                thislldo = True
                index = 0
                for foot in pat:
                    index += int(foot)
                    if scansion[index-1] not in '/%':
                        thislldo = False
                        break
                if thislldo: break
            if not thislldo: return []		# no plausible pattern of feet!
            footlist = []
            f = 0
            for digit in pat:
                stride = int(digit)
                if f + stride >= len(scansion): endf = None
                else: endf = f+stride
                if AnapSubs.has_key(scansion[f:endf]):
                    footlist.append(AnapSubs[scansion[f:endf]])
                    f += stride
                else: return []
        if lastfoot: footlist.append(lastfoot)
        return footlist

    def AnapEndFoot(self, logger):
        """Initiate data for anapestic scansion; identify terminal-slack last foot."""
        marks = self.P.GetMarks()
        numsyls = len(marks)
        if not lineDat['lfeetset']:		# calculate line's foot-length
            (lineDat['lfeet'], excess) = divmod(numsyls, 3)
            if marks[-1] == 'x': excess -= 1	# term. slack doesn't add feet
            if excess > 0: lineDat['lfeet'] += 1
        if marks[-2:] == 'xx':		# mark promotion, treat as stressed (x% or /x%)
            marks = marks[:-1] + '%'
            self.P.AddScanMark('%', len(marks)-1)
        if marks[-1] == 'x':		# see AnapSubs for special notes on last feet!
            tailstart = marks.rfind('/')					# point to penult
            tailstart = marks.rfind('/', 0, tailstart)	#   stress in line
            tail = numsyls - tailstart - 1
            if AnapSubs.has_key(marks[-tail:]):
                lineDat['lastfoot'] = AnapSubs[marks[-tail:]]
            else:
                tail += 1		# desperation: one more foot to try
                tailstart -= 1
                if AnapSubs.has_key(marks[-tail:]):
                    lineDat['lastfoot'] = AnapSubs[marks[-tail:]]
                else:
                    logger.Explain("\nFAIL! unknown last foot")
                    return self.P.GetScanString(), False
            self.P.AddFootDivMark(tailstart + 1)
            lineDat['hremain'] = (0, tailstart + 1)
        else:
            lineDat['lastfoot'] = ''
            lineDat['hremain'] = (0, len(marks))
        logger.ExpAnapEnd(lineDat['lastfoot'])
        return self.P.GetScanString(), True
    
    def AnapDivideHead(self, logger):
        """Divide anapestic line (before terminal-slack last foot) into feet.
        
        If (remainder of) line is all trisyllables, identify feet. If one or more
        disyllabic feet are indicated by a short syllable-count, try various
        positions, relying on each foot ending in a stress (which would *not*
        work with iambics). Arbitrarily, we prefer leftward choices for positions
        of disyllables; experiment shows results are mixed.
        """
        needfeet = lineDat['lfeet']
        if lineDat['lastfoot']: needfeet -= 1
        marks = self.P.GetMarks()
        numsyls = lineDat['hremain'][1]		# we know hremain[0] is 0
        if numsyls > needfeet * 3:
            logger.Explain("\nFAIL! too many syllables to scan anapestically")
            return self.P.GetScanString(), False
        if numsyls == needfeet * 3:		# assign even 3s as feet
            marks = self.AnapPromoteSlack(marks, insertmark=True)
            for (footname, sylinx) in footfinder(AnapSubs, marks, 3, 0, numsyls):
                if footname: lineDat['footlist'].append(footname)
                else:
                    logger.Explain("\nFAIL! unknown foot")
                    return self.P.GetScanString(), False
                if sylinx < len(marks): 
                    self.P.AddFootDivMark(sylinx)
            logger.ExpAnapTrisyl(needfeet, lineDat['lfeet'])
        else:
            needDisyls = (needfeet * 3) - numsyls
            if needDisyls > needfeet: return self.P.GetScanString(), False
            marks = self.AnapPromoteSlack(marks, insertmark=True)
            numlist = '2' * needDisyls + '3' * (needfeet - needDisyls)
            listoflists = uniquePermutations(numlist)
            for pat in listoflists:
                thislldo = True
                index = lineDat['hremain'][0]		# we know it's 0
                for foot in pat:
                    index += int(foot)
                    if marks[index-1] not in  '/%':	# treat (term.) prom. as stress
                        thislldo = False
                        break
                if thislldo: break
            if not thislldo:
                logger.Explain("\nFAIL! could not find plausible pattern of feet")
                return self.P.GetScanString(), False
            f = sylinx = 0	# can't use footfinder; chunksize changes
            for digit in pat:
                stride = int(digit)
                if f + stride >= len(marks): endf = None
                else: endf = f+stride
                sylinx += stride
                if AnapSubs.has_key(marks[f:endf]):
                    lineDat['footlist'].append(AnapSubs[marks[f:endf]])
                    if endf: self.P.AddFootDivMark(sylinx)
                    f += stride
                else: 
                    logger.Explain("\nFAIL! unknown foot?")
                    return self.P.GetScanString(), False
            logger.ExpAnapDisyl(needfeet, lineDat['lfeet'], needDisyls)
        if lineDat['lastfoot']: lineDat['footlist'].append(lineDat['lastfoot'])
        return self.P.GetScanString(), True
    
    def AnapPromoteSlack(self, scansion, insertmark=False):
        """Replace 'x' with '%' in a run of slacks, return revised scansion.
        
        So much in anapestic scansion depends on a stress anchoring the foot
        at its end that lines with long runs of slacks (four or five) get
        rejected as unmetrical, when a human reader instead hears a stress-
        promotion. We look for four slacks (the find includes five) and mark
        the third of them as promoted; then '(anapest)' is found as the foot.
        """
        slackrun = scansion.find('xxxx')
        if slackrun != -1:
            scansion = scansion[:slackrun + 2] + '%' + scansion[slackrun + 3:]
            if insertmark: self.P.AddScanMark('%', slackrun + 2)
        return scansion

    def AnapCleanUpAndReport(self, logger):
        """Final-condition check and Explainer call to show results of anap scansion.
        
        If any internal amphibrach, return fail and make suggetion. Replace
        |x/|/x/| with |x//|x/| on general principle of greater regularity. (I say the
        bacchius is less disruptive than the cretic. This is not always right!
        but when not, it's because of syntax, which we know nothing about.)
        Call Explainer with list of feet to be displayed.
        """
        fl = lineDat['footlist']
        d = dictinvert(AnapSubs)
        substitutions = 0
        sylinx = 0
        footAdjust = False
        for finx in range(len(fl)-1):
            if fl[finx] == 'amphibrach':
                s1 = "\namphibrach (x/x) within anapestic line surely wrong; "
                s2 = "check for a word wrongly syllabified or stressed and "
                s3 = "double-click it to change"
                logger.Explain(''.join([s1, s2, s3]))
                return self.P.GetScanString(), False
            if fl[finx] == 'iamb' and fl[finx+1] == 'cretic':
                fl[finx] = 'bacchius'
                fl[finx+1] = 'iamb'
                self.P.EraseFootDivMark(sylinx + 2)
                self.P.AddFootDivMark(sylinx + 3)
                footAdjust = True
            if fl[finx] not in ('anapest', '(anapest)'):
                substitutions += 1
            sylinx += len(d[fl[finx]][0])
        if lineDat['lfeetset'] and (len(fl) != lineDat['lfeet']):
            logger.ExpAnapFinal(fl, 100)
            return self.P.GetScanString(), False
        else:
            logger.ExpAnapFinal(fl, substitutions, footAdjust)
            return self.P.GetScanString(), True
