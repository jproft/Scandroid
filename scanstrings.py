# scanstrings.py 1.2
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
# Text, strings, and generally useful globals the Scandroid needs;
# Also, the Explainer class, which gabs about what we're doing at every
# stage. Also, some non-class utility functions.

abouttxt = \
"""
    ~      ~      ~      ~      ~      ~      ~      ~      ~

scansion of English metrical verse for Mac and Windows

    ~      ~      ~      ~      ~      ~      ~      ~      ~

version 1.2, Copyright (C) 2005 Charles Hartman

the Scandroid comes with ABSOLUTELY NO WARRANTY;
for details, see the GNU Public License in the file "gpl.txt"
that accompanies the program. This software is OSI Certified 
Open Source Software. OSI Certified is a certification mark 
of the Open Source Initiative.
"""

InitialText = \
"""This is a text, iambic though inane,
Exemplifying various variations
Pentameters exhibit. It might train
Scanning, or at least run through the stations.
"""

STRESS		= '/'		# these are bogus, in that these signs are hard-
SLACK		= 'x'		#  wired into, e.g., search strings; but maybe
PROMOTED	= '%'	#  having them here will be a reminder
SYLMARK = '#'
FOOTDIV	= '|'

footDict = { 'x/':'iamb', 'xx':'pyrrhic', '//':'spondee', '/x':'trochee',
             'x/x':'amphibrach', '//x':'palimbacchius', 'xx/':'anapest',
             '/':'defective', '/xx':'dactyl', '/x/':'cretic', 'x//':'bacchius',
             'x%':'(iamb)', 'xx%':'(anapest)', '%x':'(trochee)',
             'x/xx':'2nd paeon', 'xx/x':'3rd paeon'}

AnapSubs = { 'xx/':'anapest', '/x/':'cretic', 'x//':'bacchius', 'x/':'iamb',
                 'x%':'(iamb)', 'xx%':'(anapest)', '//':'spondee', 'xx/x':'3rd paeon',
                'x/x':'amphibrach', '///':'molossus', '/x%':'(cretic)', '//x':'palimbacchius' }
##                'xx':'pyrrhic', 'xxx':'tribrach' }		# experiment!

lineLengthName = ['','','DIMETER','TRIMETER','TETRAMETER','PENTAMETER',
                            'HEXAMETER','HEPTAMETER','OCTAMETER','NONAMETER']

import wx			# only for default encoding!
defaultEncoding = wx.GetDefaultPyEncoding()

class Explainer:
    """Send pedagogically useful (?) notes to the Notes frame about each step.
    
    The top-level ScandroidFrame owns an instance of this, and sends it as an
    argument to any function in the ScansionMachine that needs to print notes
    through some member of this class.
    """
    def __init__(self, target): self.Target = target

    def Explain(self, str):		# doesn't add newlines unless told to
        """All-purpose print statement for Notes"""
        self.Target.AppendText(str)
        #self.Target.AppendText(str.encode('ascii'))
        
    def ExpDeduceParams(self, metron, linelen, linelenset):
        sall1 = "The Scandroid has sampled the lines, and deduced:\n"
        sall2 = "     -- that the basic foot is the "
        siamb = "IAMB (x/).\n"
        sanap = "ANAPEST (xx/).\n"
        snotset1 = "     -- that the lines are not consistent in length (in feet),\n"
        snotset2 = "          so it will figure length line by line, not always correctly!"
        sset1 = "     -- that the lines consistently have "
        sset2 = str(linelen)
        sset3 = " feet."
        sall3 = "\nThese conclusions could be wrong. The Scan menu lets you "
        sall4 = "force the choice of basic foot."
        if metron == 2: self.Explain(''.join([sall1, sall2, siamb]))
        else: self.Explain(''.join([sall1, sall2, sanap]))
        if linelenset: self.Explain(''.join([sset1, sset2, sset3, sall3, sall4]))
        else: self.Explain(''.join([snotset1, snotset2, sall3, sall4]))

    ## - - methods explaining normal workings of each step, each algorithm

    def ExpParseLine(self, dictwords, compwords):
        if dictwords:
            self.Explain("\nwords in the dictionary: ")
            for wd in dictwords:
                self.Explain('/' + '/'.join(syl.lower() for syl in wd) + '/')
        if compwords:
            self.Explain("\nread other words as: ")
            for wd in compwords:
                self.Explain('/' + '/'.join(syl.lower() for syl in wd) + '/ ')

    def ExpLexStress(self, dictwords, compwords):
        self.Explain("  (CAPS = stressed)\ndict. word stresses: ")
        self.Explain(str(' / ' + ' / '.join(' '.join(s.encode('utf-8') for s in w) for w in dictwords)) + ' / ')
        self.Explain("\ncalc. word stresses: ")
        self.Explain(' / ' + ' / '.join(' '.join(s.encode(defaultEncoding) for s in w) for w in compwords) + ' / ')
        self.Explain("\nany ambiguous stresses will be resolved in the next step")
        
    def ExpChooseAlg(self, alg, ambigs):
        sall1 = "\nthe Scandroid knows two approaches to dividing the line "
        sall2 = "into feet; it has tried both, and chosen "
        salg1 = "Algorithm 1 (Corral the Weird)"
        salg2 = "Algorithm 2 (Maximize the Normal)"
        sall3 = "\n(you can force the choice; see the Scan menu)"
        sambig1 = "\n\nthe program also decided one or more ambiguous stresses "
        sambig2 = "and adjusted the lexical stresses accordingly"
        if alg == 1: self.Explain(''.join([sall1, sall2, salg1, sall3]))
        else: self.Explain(''.join([sall1, sall2, salg2, sall3]))
        if ambigs > 1: self.Explain(''.join([sambig1, sambig2]))

    def ExpWeirdEnds(self, lastfoot, footlist):
        s1 = "      <begin Algorihm 1: Corral the Weird>"
        s2 = "\ncheck line for first/last feet of abnormal length:"
        self.Explain(''.join([s1, s2]))
        if footlist and (footlist[0] == 'defective'): aceph = True
        else: aceph = False
        if not lastfoot and not aceph: self.Explain("\nfound none")
        else:
            if aceph: self.Explain('\nfound acephalous ("headless") line')
            if lastfoot:
                if lastfoot == '2nd paeon':
                    self.Explain("\nfound extra slack syllables at end of line; ")
                else: self.Explain("\nfound extra slack syllable at end of line; ")
                self.Explain("last foot is %s" % lastfoot)

    def ExpFootDivision(self, currlen, normlen):
        sall = "\nthe line (or what's left over after any first/last feet) "
        if currlen == normlen:
            s1 = "has the number of syllables expected in this meter, "
            s2 = "so simply divide into normal-length feet"
        elif currlen < normlen:
            s1 = "has fewer syllables than the meter predicts, so seek "
            s2 = 'a "defective foot" (a single stress)'
        else:
            s1 = "has more syllables than the meter predicts, so seek "
            s2 = "one or more anapests (xx/) to make up the difference"
        self.Explain(''.join([sall, s1, s2]))

    def ExpREMain(self, start, length, tail, feet, totalfeet):
        s1 = "      <begin Algorihm 2: Maximize the Normal>\nLongest run of "
        s2 = "iambs (x/) and potential iambs (xx) from syllable %s " % str(start+1)
        s3 = "for %s syllables\n%s syllables left over before " % (length, start)
        s4 = "that and %s syllables after\naccounted for %s " % (tail, feet)
        s5 = "of %s feet" % totalfeet
        self.Explain(''.join([s1, s2, s3, s4, s5]))

    def ExpRECleanUp(self, head, tail, extradiv=False):
        if head: self.Explain("\ndivide extra syllables at start of line into pairs")
        if tail: self.Explain("\ndivide extra trailing syllables into pairs")
        if extradiv: 
            self.Explain("\nget rid of extra foot-division before last syllable")
        if not head and not tail and not extradiv:
            self.Explain("\nnothing to clean up at the end")

    def ExpPromotions(self, promoted):
        if not promoted: self.Explain("\n(no promoted stresses found)")
        else:
            s1 = "  ('%' used here rather than usual '(/)')"
            if len(promoted) == 1:
                s2 = "\nprobable promoted stress on this syllable:  "
            else: s2 = "\nprobable promoted stresses on these syllables:  "
            self.Explain(''.join([s1, s2]))
            self.Explain(''.join([''.join([str(p+1), '   ']) for p in promoted]))

    def ExpEndGame(self, listOfFeet, subs):
        if subs > len(listOfFeet):			# NOT >= (5-sub i.p. possible)
            self.Explain("  |  ".join([f for f in listOfFeet]))
            #for f in listOfFeet: self.Explain("  |  " + f)
            self.Explain("\nFAIL! wrong number of feet")
        else:
            s1 = "\nThe Scandroid found these feet (ones in parentheses"
            s2 = " resulting from promotions):\n\t"
            self.Explain(''.join([s1, s2]))
            self.Explain("  |  ".join([f for f in listOfFeet]))
            if subs > 1: s3 = "  |\n%s substitute feet" % subs
            else: s3 = "  |\none substitute foot"
            s4 = " -- a crude measure of complexity"
            self.Explain(''.join([s3, s4]))
            
    def ExpRestartNewIambicAlg(self, algorithm, scanline):
        if algorithm == 1:
            s1 = "\n\nAlgorithm 1 (Corral the Exceptional) FAILED\n"
            s2 = "with this result: %s" % scanline
            s3 = "\n\nTry Algorithm 2 (Maximize the Normal)\n"
        else:
            s1 = "\n\nAlgorithm 2 (Maximize the Normal) FAILED\n"
            s2 = "with this result: %s" % scanline
            s3 = "\n\nTry Algorithm 1 (Corral the Exceptional)\n"
        s4 = "\nReturn the scansion to lexical stresses only"
        self.Explain(''.join([s1, s2, s3,s4]))

    ## - - explanations for steps in anapestic scansion
    
    def ExpAnapGetBest(self, numtried, results):
        if numtried > 1:
            s1 = "\nthe program tried all %s resolutions of " % numtried
            s2 = "stress ambiguities; "
            self.Explain(''.join([s1, s2]))
        else:
            self.Explain("\nthere were no stress ambiguities to be resolved; ")
        if results:
            if results == 1:
                self.Explain("found a scannable line of lexical stresses")
            else:
                s1 = "found %s scannable lines of lexical stresses;" % results
                s2 = "chose one at random"
                self.Explain(''.join([s1, s2]))
        else:
            self.Explain("could not find a scannable line of lexical stresses")
                
    def ExpAnapEnd(self, lastfoot):
        self.Explain("\nlooked for special (terminal-slack) last feet; found ")
        if lastfoot: self.Explain(lastfoot)
        else: self.Explain("none")
        
    def ExpAnapTrisyl(self, feetfound, totalfeet):
        if totalfeet > feetfound:
            s1 = "\nbefore special last foot, line divides evenly into "
            s2 = "%s trisyllabic feet" % feetfound
        else:
            s1 = "\nline divides evenly into %s " % feetfound
            s2 = "trisyllabic feet"
        self.Explain(''.join([s1, s2]))

    def ExpAnapDisyl(self, feetfound, totalfeet, disylfeet):
        sdisyl = "\nline requires %s disyllabic feet among the " % disylfeet
        if totalfeet > feetfound:
            shead = "the remaining (pre-terminal) %s" % feetfound
        else: shead = "the %s total" % feetfound
        self.Explain(''.join([sdisyl, shead]))

    def ExpAnapFinal(self, footlist, subs, footAdjust=False):
        self.Explain("\nThe Scandroid found these feet:\n\t")
        self.Explain('  |  '.join([f for f in footlist]))
        self.Explain("  |")
        if footAdjust:
            self.Explain("\n(replaced iamb+cretic with bacchius+iamb for regularity)")
