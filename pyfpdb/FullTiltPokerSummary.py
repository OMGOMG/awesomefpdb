#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Copyright 2008-2011 Steffen Schaumburg
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, version 3 of the License.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.
#In the "official" distribution you can find the license in agpl-3.0.txt.

"""pokerstars-specific summary parsing code"""

import L10n
_ = L10n.get_translation()

from decimal_wrapper import Decimal
import datetime

from Exceptions import FpdbParseError
from HandHistoryConverter import *
from TourneySummary import *

class FullTiltPokerSummary(TourneySummary):
    limits = { 'No Limit':'nl', 'Pot Limit':'pl', 'Limit':'fl', 'LIMIT':'fl' }
    games = {                          # base, category
                              "Hold'em" : ('hold','holdem'), 
                                'Omaha' : ('hold','omahahi'),
                             'Omaha Hi' : ('hold','omahahi'),
                          'Omaha Hi/Lo' : ('hold','omahahilo'),
                            'Omaha H/L' : ('hold','omahahilo'),
                                 'Razz' : ('stud','razz'), 
                                 'RAZZ' : ('stud','razz'),
                          '7 Card Stud' : ('stud','studhi'),
                              'Stud Hi' : ('stud','studhi'),
                    '7 Card Stud Hi/Lo' : ('stud','studhilo'),
                             'Stud H/L' : ('stud','studhilo'),
                               'Badugi' : ('draw','badugi'),
              'Triple Draw 2-7 Lowball' : ('draw','27_3draw'),
                      '2-7 Triple Draw' : ('draw','27_3draw'),
                          '5 Card Draw' : ('draw','fivedraw'),
                         '7-Game Mixed' : ('mixed','7game'),
                        '10-Game Mixed' : ('mixed','10game'),
                                'HORSE' : ('mixed','horse'),
               }

    substitutions = {
                     'LEGAL_ISO' : "USD|EUR|GBP|CAD|FPP|FTP",      # legal ISO currency codes
                            'LS' : u"\$|\xe2\x82\xac|\u20ac|", # legal currency symbols - Euro(cp1252, utf-8)
                           'TAB' : u"-\u2013'\s\da-zA-Z#_\.",      # legal characters for tablename
                           'NUM' : u".,\d",                    # legal characters in number format
                    }

    re_TourNo = re.compile("\#(?P<TOURNO>[0-9]+),")
    re_TourneyInfo = re.compile(u"""
                        \((?P<TOURNO>[0-9]+)\)
                        (\s+)?(\sMatch\s\d\s)?
                        (?P<GAME>Hold\'em|Razz|RAZZ|7\sCard\sStud|7\sCard\sStud\sHi/Lo|Stud\sH/L|Stud\sHi|Omaha|Omaha\sHi|Omaha\sHi/Lo|Omaha\sH/L|Badugi|Triple\sDraw\s2\-7\sLowball|2-7\sTriple\sDraw|5\sCard\sDraw|7-Game\sMixed|HORSE|10-Game\sMixed)\s+
                        ((?P<LIMIT>No\sLimit|Limit|LIMIT|Pot\sLimit)\s+)?
                        (Buy-In:\s[%(LS)s]?(?P<BUYIN>[%(NUM)s]+)(\sFTP)?(\s\+\s[%(LS)s]?(?P<FEE>[%(NUM)s]+)(\sFTP)?)?\s+)?
                        (Knockout\sBounty:\s[%(LS)s](?P<KOBOUNTY>[%(NUM)s]+)\s+)?
                        ((?P<PNAMEBOUNTIES>.{2,15})\sreceived\s(?P<PBOUNTIES>\d+)\sKnockout\sBounty\sAwards?\s+)?
                        (Add-On:\s[%(LS)s](?P<ADDON>[%(NUM)s]+)\s+)?
                        (Rebuy:\s[%(LS)s](?P<REBUYAMT>[%(NUM)s]+)\s+)?
                        ((?P<P1NAME>.{2,15})\sperformed\s(?P<PADDONS>\d+)\sAdd-Ons?\s+)?
                        ((?P<P2NAME>.{2,15})\sperformed\s(?P<PREBUYS>\d+)\sRebuys?\s+)?
                        (Buy-In\sChips:\s(?P<CHIPS>\d+)\s+)?
                        (Add-On\sChips:\s(?P<ADDONCHIPS>\d+)\s+)?
                        (Rebuy\sChips:\s(?P<REBUYCHIPS>\d+)\s+)?
                        (?P<ENTRIES>[0-9]+)\sEntries\s+
                        (Total\sAdd-Ons:\s(?P<ADDONS>\d+)\s+)?
                        (Total\sRebuys:\s(?P<REBUYS>\d+)\s+)?
                        (Total\sPrize\sPool:\s[%(LS)s]?(?P<PRIZEPOOL>[%(NUM)s]+)(\sFTP)?\s+)?
                        (Top\s(\d+\s)?finishers?\sreceives?\s.+\s+)?
                        (Target\sTournament\s.+\s+)?
                        Tournament\sstarted:\s
                        (?P<DATETIME>((?P<Y>[\d]{4})\/(?P<M>[\d]{2})\/(?P<D>[\d]+)\s+(?P<H>[\d]+):(?P<MIN>[\d]+):(?P<S>[\d]+)\s??(?P<TZ>[A-Z]+)\s|\w+,\s(?P<MONTH>\w+)\s(?P<DAY>\d+),\s(?P<YEAR>[\d]{4})\s(?P<HOUR>\d+):(?P<MIN2>\d+)))
                               """ % substitutions ,re.VERBOSE|re.MULTILINE|re.DOTALL)

    re_Currency = re.compile(u"""(?P<CURRENCY>[%(LS)s]|FPP|FTP)""" % substitutions)

    re_Player = re.compile(u"""(?P<RANK>[\d]+):\s(?P<NAME>[^,\r\n]{2,15})(,\s(?P<CURRENCY>[%(LS)s])(?P<WINNINGS>[.\d]+))?(,\s(?P<TICKET>Step\s(?P<LEVEL>\d)\sTicket))?""" % substitutions)
    re_Finished = re.compile(u"""(?P<NAME>[^,\r\n]{2,15}) finished in (?P<RANK>[\d]+)\S\S place""")

    re_DateTime = re.compile("\[(?P<Y>[0-9]{4})\/(?P<M>[0-9]{2})\/(?P<D>[0-9]{2})[\- ]+(?P<H>[0-9]+):(?P<MIN>[0-9]+):(?P<S>[0-9]+)")

    codepage = ["utf-16", "cp1252", "utf-8"]

    @staticmethod
    def getSplitRe(self, head):
        re_SplitTourneys = re.compile("^Full Tilt Poker Tournament Summary")
        return re_SplitTourneys

    def parseSummary(self):
        m = self.re_TourneyInfo.search(self.summaryText[:2000])
        if m == None:
            tmp = self.summaryText[0:200]
            log.error(_("FullTiltPokerSummary.parseSummary: '%s'") % tmp)
            raise FpdbParseError

        #print "DEBUG: m.groupdict(): %s" % m.groupdict()
        rebuyCounts = {}
        addOnCounts = {}
        koCounts = {}
        mg = m.groupdict()
        if 'TOURNO'    in mg: self.tourNo = mg['TOURNO']
        if 'LIMIT'     in mg and mg['LIMIT'] != None:
            self.gametype['limitType'] = self.limits[mg['LIMIT']]
        else:
            self.gametype['limitType'] = 'mx'
        if 'GAME'      in mg: self.gametype['category']  = self.games[mg['GAME']][1]
        if mg['BUYIN'] != None:
            self.buyin = int(100*Decimal(self.clearMoneyString(mg['BUYIN'])))
        if mg['FEE'] != None:
            self.fee   = int(100*Decimal(self.clearMoneyString(mg['FEE'])))
        if 'PRIZEPOOL' in mg:
            if mg['PRIZEPOOL'] != None: self.prizepool = int(Decimal(self.clearMoneyString(mg['PRIZEPOOL'])))
        if 'ENTRIES'   in mg:
            self.entries = mg['ENTRIES']
        if 'REBUYAMT'in mg and mg['REBUYAMT'] != None:
            self.isRebuy   = True
            self.rebuyCost = int(100*Decimal(self.clearMoneyString(mg['REBUYAMT'])))
        if 'ADDON' in mg and mg['ADDON'] != None:
            self.isAddOn = True
            self.addOnCost = int(100*Decimal(self.clearMoneyString(mg['ADDON'])))
        if 'KOBOUNTY' in mg and mg['KOBOUNTY'] != None:
            self.isKO = True
            self.koBounty = int(100*Decimal(self.clearMoneyString(mg['KOBOUNTY'])))
        if 'PREBUYS' in mg and mg['PREBUYS'] != None:
            rebuyCounts[mg['P2NAME']] = int(mg['PREBUYS'])
        if 'PADDONS' in mg and mg['PADDONS'] != None:
            addOnCounts[mg['P1NAME']] = int(mg['PADDONS'])
        if 'PBOUNTIES' in mg and mg['PBOUNTIES'] != None:
            koCounts[mg['PNAMEBOUNTIES']] = int(mg['PBOUNTIES'])
        
        datetimestr = ""
        if mg['YEAR'] == None:
            datetimestr = "%s/%s/%s %s:%s:%s" % (mg['Y'], mg['M'], mg['D'], mg['H'], mg['MIN'], mg['S'])
            self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%m/%d %H:%M:%S")
        else:
            datetimestr = "%s/%s/%s %s:%s" % (mg['YEAR'], mg['MONTH'], mg['DAY'], mg['HOUR'], mg['MIN2'])
            self.startTime = datetime.datetime.strptime(datetimestr, "%Y/%B/%d %H:%M")

        if 'TZ' in mg and mg['TZ'] is not None:
            self.startTime = HandHistoryConverter.changeTimezone(self.startTime, mg['TZ'], "UTC")


        m = self.re_Currency.search(self.summaryText)
        if m == None:
            log.error("FullTiltPokerSummary.parseSummary: " + _("Unable to locate currency"))
            raise FpdbParseError
        #print "DEBUG: m.groupdict(): %s" % m.groupdict()

        mg = m.groupdict()
        
        if mg['CURRENCY'] == "$":     self.buyinCurrency="USD"
        elif mg['CURRENCY'] == u"€":  self.buyinCurrency="EUR"
        elif mg['CURRENCY'] == "FPP": self.buyinCurrency="FTFP"
        elif mg['CURRENCY'] == "FTP": self.buyinCurrency="FTFP"
        if self.buyin ==0:            self.buyinCurrency="FREE"
        self.currency = self.buyinCurrency

        m = self.re_Player.finditer(self.summaryText)
        playercount = 0
        for a in m:
            mg = a.groupdict()
            #print "DEBUG: a.groupdict(): %s" % mg
            name = mg['NAME']
            rank = int(mg['RANK'])
            winnings = 0
            rebuyCount = 0
            addOnCount = 0
            koCount = 0

            if 'WINNINGS' in mg and mg['WINNINGS'] != None:
                winnings = int(100*Decimal(mg['WINNINGS']))
                if mg['CURRENCY'] == "$":     self.currency="USD"
                elif mg['CURRENCY'] == u"€":  self.currency="EUR"
                elif mg['CURRENCY'] == "FPP": self.currency="FTFP"
                elif mg['CURRENCY'] == "FTP": self.currency="FTFP"
                
            if name in rebuyCounts:
                rebuyCount = rebuyCounts[name]
            
            if name in addOnCounts:
                addOnCount = addOnCounts[name]
                
            if name in koCounts:
                koCount = koCounts[name]
                
            if 'TICKET' and mg['TICKET'] != None:
                #print "Tournament Ticket Level %s" % mg['LEVEL']
                step_values = {
                                '1' :    '330', # Step 1 -    $3.30 USD
                                '2' :    '870', # Step 2 -    $8.70 USD
                                '3' :   '2600', # Step 3 -   $26.00 USD
                                '4' :   '7500', # Step 4 -   $75.00 USD
                                '5' :  '21600', # Step 5 -  $216.00 USD
                                '6' :  '64000', # Step 6 -  $640.00 USD
                                '7' : '210000', # Step 7 - $2100.00 USD
                              }
                winnings = step_values[mg['LEVEL']]    
                
            self.addPlayer(rank, name, winnings, self.currency, rebuyCount, addOnCount, koCount)

            playercount += 1


        # Some files dont contain the normals lines, and only contain the line
        # <PLAYER> finished in XXXXrd place
        if playercount == 0:
            m = self.re_Finished.finditer(self.summaryText)
            for a in m:
                winnings = 0
                name = a.group('NAME')
                rank = a.group('RANK')
                self.addPlayer(rank, name, winnings, self.currency, 0, 0, 0)
