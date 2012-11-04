# scanpositions.py 1.2
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
# This module of the Scandroid contains the class for the Positioner.
# Previous experience shows that the infrastructure required to display
# the marks decided by the real scansion routines is a major, trivial, 
# endless headache. Also there are various ways to do it -- for example,
# allowing for proportional fonts. Also it's really GUI stuff anyway. All
# of which argues for a separate package of all routines that massage 
# scansion-mark data for display and preserve it for manipulation.
#
# SO-FAR UNUSED: all code involving P.promCands and P.wordbounds is
# requiring a few CPU cycles and not contributing anything. If more adjustments
# to promotions (especially in iambics) end up using them, good. If not,
# sooner or later these lines should be deleted.

import sre
import copy
from scanstrings import *
from scanutilities import *

class Positioner:
    def __init__(self):
        self.charlist = []		# one item per char in the printed line of text
        self.sylmids = []		# indices of positions of middles of syllables
        self.footplace = [0]		# indices of positions of possible foot divs
        self.possLexicals = []	# list of scanstrings, ambiguities resolved
        self.punctAt = []		# to check on caesurae
        self.promCands = []
        self.wordbounds = []	# index of pos after each word (NOT USED)
        self.scanMarkMoved = False	# silly flag; see FindEmptyPosForMark
    
    def NewLine(self, linelength):
        self.charlist = (linelength + 1) * [' ']	# extra for possible footdiv
        self.sylmids = []
        self.footplace = [0]			# keep 0-based, parallel to sylmids[]
        self.possLexicals = []
        self.punctAt = []
        self.promCands = []
        self.wordbounds = []

    def AddWord(self, syls, linePos):
        """Add data of syllables of a word to this class's various data structures.
        
        This function has grown. It tracks not only the midpoint of each 
        syllable in the printed line (sylmids) and its end (a possible foot-
        division point), and stress or slack marks to the spaced-out line
        (charlist), but also tracks ambiguous stresses (multiplying the lines
        of possible lexical marks) and candidates for promotion.
        """
        self.promCands.extend([0 for x in range(len(syls))])
        sylinx = len(self.sylmids)
        # if punct followed prev word, first of this word good for promotion
        if self.wordbounds and self.punctAt:
            if self.wordbounds[-1] == self.punctAt[-1]:
                self.promCands[sylinx] += 1
        ambiguous = True
        if len(syls) == 1:			# special code in dictionary
            self.promCands[sylinx] += 1	# any monosyl good for promotion 
            if syls[0][-1] != '*': ambiguous = False
            else:
                syls[0] = syls[0][:-1]	# remove code '*'
                self.promCands[sylinx] += 1	# plus for stress-ambiguous
        else:		# stress-ambig = absence of all-caps syllable
            for s in syls:
                if s.isupper():			# enforces ALL CAPS rule!
                    ambiguous = False
                    break
        if ambiguous:
            if len(self.possLexicals) == 0:
                self.possLexicals.append(self.GetMarks())
            halfway = len(self.possLexicals)
            self.possLexicals *= 2			# each amgibuity doubles the list
            for pL in range(0, halfway):
                if len(syls) == 1: self.possLexicals[pL] += STRESS
                else: self.possLexicals[pL] += (STRESS + SLACK)
            for pL in range(halfway, len(self.possLexicals)):
                if len(syls) == 1: self.possLexicals[pL] += SLACK
                else: self.possLexicals[pL] += (SLACK + STRESS)
        for s in syls:
            self.sylmids.append(linePos + (len(s) // 2))
            if s.isupper(): newmark = STRESS	# enforces ALL CAPS rule!
            else: newmark = SLACK
            self.AddScanMark(newmark, len(self.sylmids) - 1)
            if not ambiguous:		# if ambig, this is already done
                for pL in range(len(self.possLexicals)):
                    self.possLexicals[pL] += newmark
            linePos += len(s)
        self.wordbounds.append(linePos)	# not used (punct only); but...
        return linePos

    def LocateFootDivPositions(self):
        """Record positions for potential foot divs halfway between syllable middles.

        The array of positions is initialized with 0 by NewLine; so item n in this
        array corresponds to a foot-division spot *before* (at the beginning of)
        syllable n as recorded in self.sylmids. (Arbitrary but consistent.)
        """
        for syl in range(len(self.sylmids) - 1):
            self.footplace.append(self.sylmids[syl] + (self.sylmids[syl + 1]
                                                       - self.sylmids[syl]) // 2)
        self.footplace.append(len(self.charlist) - 1)
    
    def AddPunct(self, str, linePos):
        for c in str:			# skip spaces, record punct for (?) later use
            if not c.isspace():
                self.charlist[linePos] = c
                self.punctAt.append(linePos)
            linePos += 1
        return linePos
    
    def AddScanMark(self, mark, syllable):
        """Insert given mark into charlist of (spaced) scansion marks.
        
        Place mark ('/', 'x', or '%') over the middle of the syllable. Note
        that 'syllable' means something diffeernt in AddFootDivMark().
        """
        if syllable > len(self.sylmids): return		# major woops
        self.charlist[self.sylmids[syllable]] = mark
    
    def AddFootDivMark(self, syllable):
        """Place a foot-division mark *before* the specified syllable."""
        if syllable > len(self.sylmids):
            return						# should never happen
        if syllable == len(self.sylmids):		# special: temp eol mark
            pos = len(self.charlist) - 1
        else: pos = self.footplace[syllable]
        pos = self.FindEmptyPosForMark(pos)
        self.charlist[pos] = FOOTDIV
    
    def EraseFootDivMark(self, syllable):
        """Replace internal-to-line footdiv with space to "move" a footdiv."""
        self.charlist[self.footplace[syllable]] = ' '
    
    def FindEmptyPosForMark(self, pos):
        """Find a nondestructive spot for a footdiv mark.
        
        Since the footdiv mark goes *before* the given syllable index, any
        scansion mark in this position needs to be moved leftward to be saved
        and still in its correct foot. If the position we want has a scansion 
        mark in it, try moving the footdiv right by one, except in the special
        case of start of line (see below). If that position is full too, we look
        leftward for the first available unmarked space and move everything
        between there and here left by one, freeing our position.
        
        Another twist: iambic algorithm 2 can temporarily put a footdiv mark
        at the very start of the line. This requires a special case here -- *and*
        a class data-member that flags that this has been done. Ick.

        This can silently overwrite marks of punctuation in charlist.
        We don't need them by this time, so it should be OK.
        """
        SCANMARKS = 'x/%'
        if self.charlist[pos] not in SCANMARKS: return pos
        if pos == 0 and self.charlist[0] in SCANMARKS:
            self.charlist[1] = self.charlist[0]
            self.scanMarkMoved = True		# flag to move back later!
            return pos
        if pos < len(self.charlist) - 1 and self.charlist[pos+1] not in SCANMARKS:
            return pos + 1
        blank = pos
        while blank > 0 and self.charlist[blank] in SCANMARKS: blank -= 1
        for s in range(blank, pos):
            self.charlist[s] = self.charlist[s+1]
        return pos

    def GetAmbiguities(self):
        """Return list of 1 or more possible resolutions of stress ambiguities"""
        if len(self.possLexicals) > 0: return self.possLexicals
        else: return [self.GetMarks()]

    def GetMarks(self, includeFeet=False):
        """Return unspaced line of marks: x, /, and |"""
        return ''.join(self.GetScanString(includeFeet).split())

    def GetScanString(self, feet = True, punct = False, sylsOnly = False):
        """Return fully spaced line of all scansion marks (with options)"""
        s = ''.join(self.charlist)
        if not feet or sylsOnly: s = sre.sub('\|', ' ', s)
        if not punct or sylsOnly: s = sre.sub('[-.,;:?!\(\)\"\']', ' ', s)
        if sylsOnly: s = sre.sub('[^ ]', SYLMARK, s)
        return s
    
    def AdjustMarks(self, scansion):
        """Correct marks in charlist to correspond to given scansion.
        
        This is called by SM.ChooseAlgorithm and SM.GetBestAnapLexes after
        each has decided on the best among possible lexical stresses. While
        deciding, it will have put various / and x marks in charlist, and the
        last one tried will likely not have been the one finally chosen, so we
        correct the condition of charlist to reflect the final choice.
        """
        i = 0		# index in unspaced line of marks
        for c in range(len(self.charlist)):	# index in spaced line
            if self.charlist[c] in 'x/':
                self.charlist[c] = scansion[i]
                i += 1
            if i >= len(scansion):
                break
    
    def RemoveEndFootMarks(self):
        """Per convention, erase foot-division marks at start and end of line.
        
        This function is now called *only* at the beginning of the second step of
        the second iambic algorithm. There for expository purposes we need to
        show the bounds of the "regular" stretch, which may entail marks at the
        ends of the line, which it's against convention to show.
        
        A special case: if there was a scansion mark at the very start of the 
        line, it will have been moved to make way for the footdiv mark. If the
        flag for this is set we put the mark back where it was.
        """
        self._removeTailFootMark()
        self._removeHeadFootMark()
    
    def _removeTailFootMark(self):
        lastfootdiv = ''.join(self.charlist).rfind(FOOTDIV)
        if lastfootdiv == -1:
            return
        islastmark = True
        for c in self.charlist[lastfootdiv:]:
            if c in 'x/%':		# some scan mark follows last footdiv
                islastmark = False
                break
        if islastmark:
            self.charlist[lastfootdiv] = ' '
    
    def _removeHeadFootMark(self):
        if self.charlist[0] == FOOTDIV:
            if self.scanMarkMoved:
                self.charlist[0] = self.charlist[1]
                self.charlist[1] = ' '
                self.scanMarkMoved = False
            else:
                self.charlist[0] = ' '
 
    def FeetAtPunctBounds(self, footlist):
        d = dictinvert(footDict)
        retlist = [True]
        i = 0
        for f in footlist:
            i += len(d[f][0])		# invert turns strings to *lists* of one string each
            if i >= len(self.footplace):
                return retlist
            ip = self.footplace[i]
            while ip:
                if ip in self.punctAt:
                    retlist.append(True)
                    break
                elif self.charlist[ip] in 'x/%':
                    retlist.append(False)
                    break
                ip -= 1
        return retlist
