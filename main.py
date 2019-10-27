#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  main.py
#  
#  Copyright 2019 jdub <jdub@compy2>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  


'''
TODO:
for some reason the amount being stored is       


'''



import dbconnector as db

CURRENT_EXCHANGE_RATE = 1.32

cnx = db.getConnectionToMySQL()
cursor = db.getCursorFromConnection(cnx)
curs = db.enterBudgetDB(cursor)

db.dropTables(curs)
db.createTables(curs)

f = open("test.csv", "r")
skippedFirstLine = False

for line in f:
    if not skippedFirstLine:
        skippedFirstLine = True
        continue
    entries = line.split(",")
    account = entries[0]
    date = db.reformatDate(entries[2])
    desc_one = entries[4]
    desc_two = entries[5]
    amt_cad = entries[6]
    amt_usd = entries[7]

    if amt_usd:
        amt_cad = round(amt_usd * CURRENT_EXCHANGE_RATE, 2)
    else:
        amt_cad = float(amt_cad)
    fullDesc = db.formatDescriptionForMYSQL([desc_one, desc_two])
    
    #debits are denoted as negative values, so switch this for the script
    amt_cad *= -1
    
    

    if db.elementIsInIgnoreTable(fullDesc):
        print("{} in ignore table".format(fullDesc))
        continue

    # TODO: this isn't implemented at all yet
    #expendID = db.getExpenditureID(date, account)

    
    
    
    # This does NOT add it to the desc table
    description = db.getShortHandVersionOfDesc(fullDesc)
# UP TO THIS POINT, EVERYTHING IS USING ONE LONE DESCRIPTION.
# FROM HERE, description SHOULD BE THE ONLY DESCRIPTION USED.
# THIS IS BEING STORED IN THE "description" DATABASE.        
    
    ass = db.isInAssignments(description)
    print("DFGDGFDFGD")
    print(ass)

    if ass:
        #TODO: Add to assignments
        print("Would start creating transactions as there are assignments found")
        
    if not db.isInDescriptionTable(description):
        #add it to the description table
        db.addToDescription(description)
        
    
        assignments = {}
        percentageLeftToAssign = 100
        while percentageLeftToAssign > 0:
            print("desc: {}\nPerc: {}".format(description, percentageLeftToAssign))
            res = db.mapDescriptionToTypeID(description, percentageLeftToAssign)
            if not res:
                percentageLeftToAssign = 0
                continue
            else:
                typeID, percentage = res
            print("typeid: {}\nPerc: {}".format(typeID, percentage))
            #This means to
            assignments.update({typeID: percentage})
            percentageLeftToAssign -= percentage
        assignmentIDs = []
        for typeID, percentage in assignments.items():
            #Add to assignments table
            print("Desc: {},  TypeID: {},  Percentage: {}".format(description, typeID, percentage))
            
            db.addToAssignments(description, typeID, percentage)

            #add investment
            print(amt_cad)
            amount = round((percentage * .01) * amt_cad, 2)
            print(amt_cad)
            investID = db.getInvestmentID(typeID, amount)
            
            #add transaction
            db.addToTransaction(expendID, investID)

 
    
 
