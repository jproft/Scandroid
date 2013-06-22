# dictfuncs.py 1.5
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
# This module holds the class that, rather loosely, contains methods and
# structures connected with the dictionary of syllable-and-stress exceptions.

import wx
import os

from scandictionary import scandict

# added code by Thomas Heller to find "home" directory (where dictionary
# should be found), whether running from script or frozen
import imp, sys

def main_is_frozen():
    return (hasattr(sys, "frozen") or hasattr(sys, "importers") or
            imp.is_frozen("__main__"))

class ScanDict:

    def __init__(self, parent):
        self.Dict = {}
        self.mom = parent
        self.dictopen = ''		# fill in on (first) successful open
        self.LoadDictionary()
        
    def LoadDictionary(self):
        """Sets the imported dictionary to self.Dict"""
        self.Dict = scandict

    def EditDict(self, selstring):
        """Show how dict or calculation treats a word, get user's correction.
        
        If user enters new syllabification and stress for word, enter the word
        (if it was not in the dictionary) or the corrected syl-list (if it was).
        Otherwise leave it alone. Called by mouse-drive function in the
        StyledTextCtrl in scanstc.py.
        """
        word = selstring.lower()			# stripped in scanstc.py before it gets here
        if self.Dict.has_key(word): syls = self.Dict[word]
        else: syls = self.mom.S.Syllabize(word)
        s = ''
        for syl in syls: s += syl + ' '
        dlg = DictEditDialog(self, -1, s)
        val = dlg.ShowModal()
        if val == wx.ID_OK:
            newsyls = dlg.CorrectedWord
            # should undoubtedly do some very careful checking of this!
            if newsyls:
                syls = newsyls
                self.Dict[word] = syls.split()		# change dict but NOT SAVED TO FILE
            dlg.Destroy()
            return True
        else:
            dlg.Destroy()
            return False
        

class DictEditDialog(wx.Dialog):
    def __init__(self, parent, id, wordSyls):
        wx.Dialog.__init__(self, None, id, style=wx.DEFAULT_DIALOG_STYLE |
                           wx.RESIZE_BORDER)
        self.textline1 = wx.StaticText(self, -1, "     The Scandroid thinks the word     ")
        self.textline2 = wx.StaticText(self, -1, "has this pattern of syllables")
        self.textline3 = wx.StaticText(self, -1, "and stress:")
        self.wordAsKnown = wx.TextCtrl(self, -1, "")
        self.wordAsKnown.AppendText(wordSyls)
        self.wordAsKnown.SetEditable(0)
        self.textline4 = wx.StaticText(self, -1, "Type in the corrected form,")
        self.textline5 = wx.StaticText(self, -1, "separating syllables with	spaces,")
        self.textline6 = wx.StaticText(self, -1, "the stressed one ALL CAPS:")
        self.wordCorrected = wx.TextCtrl(self, -1, "")
        self.OKbutton = wx.Button(self, wx.ID_OK, " OK ")
        self.OKbutton.SetDefault()
        self.CancelButton = wx.Button(self, wx.ID_CANCEL, " Cancel ")
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.Add((20, 20), 0)
        mainsizer.Add(self.textline1, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 3)
        mainsizer.Add(self.textline2, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 3)
        mainsizer.Add(self.textline3, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 3)
        mainsizer.Add((20,20),0)
        field1sizer = wx.BoxSizer(wx.HORIZONTAL)
        field1sizer.Add((40,20),0)
        field1sizer.Add(self.wordAsKnown, 3, wx.EXPAND)
        field1sizer.Add((40,20,),0)
        mainsizer.Add(field1sizer, 0, wx.EXPAND, 3)
        mainsizer.Add((20,20),0)
        mainsizer.Add(self.textline4, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 3)
        mainsizer.Add(self.textline5, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 3)
        mainsizer.Add(self.textline6, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 3)
        mainsizer.Add((20,20), 0)
        field2sizer = wx.BoxSizer(wx.HORIZONTAL)
        field2sizer.Add((40,20),0)
        field2sizer.Add(self.wordCorrected, 3, wx.EXPAND)
        field2sizer.Add((40,20),0)
        mainsizer.Add(field2sizer, 0, wx.EXPAND, 3)
        mainsizer.Add((20,20),0)
        buttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonsizer.Add((30,30),0)
        buttonsizer.Add(self.OKbutton, 0, wx.ALIGN_LEFT)
        buttonsizer.Add((20,30),0)
        buttonsizer.Add(self.CancelButton, 0, wx.ALIGN_RIGHT)
        mainsizer.Add(buttonsizer, 0, wx.ALIGN_CENTER); mainsizer.AddSpacer((20,20),0)
        self.Bind(wx.EVT_BUTTON, self.OnOK, self.OKbutton)
        self.SetSizer(mainsizer); self.SetAutoLayout(True)
        mainsizer.Fit(self)
        self.wordCorrected.SetFocus()
        
    def OnOK(self, event):
        """When DictEditDialog's OK button is pressed, save the selected word."""
        self.CorrectedWord = self.wordCorrected.GetValue()
        event.Skip()


if __name__ == '__main__':
    app = wx.PySimpleApp()
    appframe = wx.Frame(None, -1, "the Scandroid")
    appframe.Show()
    sd = ScanDict(None)
    sd.EditDict('inane')
