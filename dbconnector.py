#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  dbconnector.py
#
#  Copyright 2019 Joe Westra <me@joewestra.ca>
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
    -Display summary of investments, etc.
    -Health check for data base?  Determine if all the tables are present

    -Modify this app for multiple users:
        DATABASE:
            -change the main database name (BUDGET) to the logged in username
            -modify structure so that the shorthand descriptions can be shared between users
'''

import mysql.connector
import queue
import errno
import os
from pathlib import Path

TABLE_LIST = ['assignment', 'category', 'description', 'domain', 'investment', 'transaction', 'type', 'expenditure', 'descs_to_ignore']
curs = ""


class DBConnection:
    """
    A convenience class to be used as an active MySQL DB connection.

    This class replaces the need to create multiple DB connections within
    separate methods.
    """

    # Dict to hold DB login credentials
    creds = {}

    # Mysql connection variables
    curs = cnx = cursor = None
    database = "BUDGET"


    def getCredentials(self):
        '''
        Opens plain test file at ./resoures/credentials and parses authentication
        parameters; one key=value combination per line.
        Can throw file not found exception.
        '''
        file = open(Path.cwd() / 'resources' / 'credentials')
        for line in file:
            # authentication parameters are stored in 'pass=1234' format
            k, v = line.strip().split("=")
            self.creds[k] = v

    def enterBudgetDB(self):
        '''
            Attempts to enter the BUDGET database.  Will create
            the database if it does not exist.
        '''
        try:
            self.cursor.execute("USE {}".format(self.database))
            return self.cursor
        except mysql.connector.Error as err:
            print("Database {} does not exist.".format(self.database))
            print(err)
            
            if err.errno == 1049:
                print("Database does not exist, attempting to create and enter it now.")
                self.createDatabase()
                return self.enterBudgetDB()
            else:
                print(err)
                return None


    def __init__(self):
        if not self.creds:
            self.getCredentials()
        self.cnx = mysql.connector.connect(**self.creds)
        self.cursor = self.cnx.cursor()
        self.curs = self.enterBudgetDB()




    def __enter__(self):
        if not self.creds:
            self.getCredentials()
        self.cnx = mysql.connector.connect(**self.creds)
        self.cursor = self.cnx.cursor()
        self.curs = self.enterBudgetDB()
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cnx.close()


    def createDatabase(self):
        try:
            self.cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(self.database))
            self.cursor.fetchall()
            print("Database {} created".format(self.database))
            return self.cursor
        except mysql.connector.Error as err:
            print("Failed creating database {}".format(self.database))
            return None



def dropTables():
    with DBConnection() as dbcnx:
        q = queue.Queue()
        for table in TABLE_LIST:
            q.put(table)

        while (not q.empty()):
            tname = q.get()
            try:
                dbcnx.curs.execute("DROP TABLE %s" % tname)

                # Forgeign key constraints may fail if dependent tables are
                # not dropped first.  This can be remedied by adding the
                # undroppable table table to the queue again, for iterative
                # removal.
            except mysql.connector.Error as err:
                print(err)
                q.put(tname)

        return True



def createTables():
    with DBConnection() as dbcnx:

        # used to show potential errors encountered
        #dbcnx.curs.execute("SHOW ENGINE INNODB STATUS")
        #print(dbcnx.curs.fetchall())

        #create the tables for the transaction logging
        dbcnx.curs.execute("CREATE TABLE domain (name VARCHAR(255) UNIQUE NOT NULL PRIMARY KEY)")
        dbcnx.curs.execute("CREATE TABLE category (name VARCHAR(255) UNIQUE NOT NULL PRIMARY KEY)")
        dbcnx.curs.execute("CREATE TABLE type (id mediumint(5) unsigned AUTO_INCREMENT not null primary key, category VARCHAR(255) not null, domain VARCHAR(255) not null, FOREIGN KEY(category) REFERENCES category(name) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY(domain) REFERENCES domain(name) ON DELETE CASCADE ON UPDATE CASCADE)")
        dbcnx.curs.execute("CREATE TABLE investment (id mediumint(5) unsigned AUTO_INCREMENT not null primary key, type mediumint(5) unsigned not null, amount DECIMAL(7,2) not null, FOREIGN KEY(type) REFERENCES type(id) ON DELETE CASCADE ON UPDATE CASCADE)")
        dbcnx.curs.execute("CREATE TABLE expenditure (id mediumint(5) unsigned AUTO_INCREMENT primary key, date DATE not null, account VARCHAR(10) NOT NULL)")
        dbcnx.curs.execute("CREATE TABLE transaction (id mediumint(5) unsigned AUTO_INCREMENT primary key, expenditure mediumint(5) unsigned NOT NULL, investment mediumint(5) unsigned NOT NULL, FOREIGN KEY(expenditure) REFERENCES expenditure(id) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY(investment) REFERENCES investment(id) ON DELETE CASCADE ON UPDATE CASCADE)")

        #create the tables for mapping Transaction Description Names to categories and percentages
        dbcnx.curs.execute("CREATE TABLE description (name VARCHAR(255) UNIQUE NOT NULL PRIMARY KEY)")
        dbcnx.curs.execute("CREATE TABLE descs_to_ignore (name VARCHAR(255) UNIQUE NOT NULL PRIMARY KEY)")
        dbcnx.curs.execute("CREATE TABLE assignment (id mediumint(5) unsigned AUTO_INCREMENT primary key, descr VARCHAR(255)NOT NULL, percentage FLOAT(3,2) not null, type mediumint(5) unsigned, FOREIGN KEY(type) REFERENCES type(id) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY(descr) REFERENCES description(name) ON DELETE CASCADE ON UPDATE CASCADE)")



def addNameElementToTable(table, name):
    with DBConnection() as dbcnx:
        try:
            dbcnx.curs.execute('INSERT INTO %s  VALUES ("%s")' % (table, name))
            dbcnx.cnx.commit()
            return True
        except mysql.connector.Error as err:
            print(err)
            return False


def addToDomain(name):
    return addNameElementToTable("domain", name)

def addToCategory(name):
    return addNameElementToTable("category", name)

def addToIgnore(name):
    return addNameElementToTable("descs_to_ignore", name)

def addToDescription(name):
    return addNameElementToTable("description", name)


def elementIsInTable(table, field, element):
    with DBConnection() as dbcnx:
        dbcnx.curs.execute("SELECT * FROM %s WHERE %s = '%s'" % (table, field, element))
        results = dbcnx.cursor.fetchall()
        if (not results):
            return False
        return True

def isInDescriptionTable(description):
    return elementIsInTable("description", "name", description)

def isInAssignments(description):
    with DBConnection() as dbcnx:
        dbcnx.curs.execute("SELECT percentage, type FROM assignment where descr = '%s'" % (description))
        results = dbcnx.cursor.fetchall()
        print("printing result set for isinassignments")
        print(results)
        print("printing done")
        return results


def shortHandVersionInTable(element, tableName):
    '''
    Searches for truncated version of the charge name within the database
    '''
    with DBConnection() as dbcnx:
        dbcnx.curs.execute("SELECT * FROM  {}".format(tableName))
        results = dbcnx.cursor.fetchall()
        for r in results:
            cleanedDesc = r[0]
            if cleanedDesc and cleanedDesc in element:
                #print("Cleaned desc = %s" % cleanedDesc)
                #print("element = %s" % element)
                print("{} entry in {} caught {}".format(cleanedDesc, tableName, element))
                return cleanedDesc
        return False

def elementIsInIgnoreTable(element):
    return(shortHandVersionInTable(element, "descs_to_ignore"))


def elementIsInDescriptionTable(element):
    return(shortHandVersionInTable(element, "description"))

def getShortHandVersionOfDesc(fullDesc):
    shortenedVersion = elementIsInDescriptionTable(fullDesc)
    if shortenedVersion:
        return shortenedVersion
    else:
        return getShortenedVersionForTable(fullDesc)


def formatDescriptionForMYSQL(description):
    formatted = ''
    for name in description:
        formatted += name.strip('\'"').replace("'","").replace('"','') + " "
    return formatted.strip()


def isInDescTable(desc):
    return elementIsInTable("description", "name", desc)


def getAllElements(table):
    with DBConnection() as dbcnx:
        dbcnx.curs.execute("SELECT * FROM %s" % table)
        results = dbcnx.cursor.fetchall()
        return results

def getPercentage(desc_one, domain, category, maximumPercentageAssignable):
    percentage = input("\nWhat percentage of a %s purchase is categorized as %s %s?  " % (desc_one, domain, category))

    try:
        percentage = int(percentage)
    except:
        print("Invalid entry, try again")
        return getPercentage(desc_one, domain, category, maximumPercentageAssignable)

    #don't assign more than 100% combined
    if percentage > maximumPercentageAssignable:
        print("That value is above the maximum percentage left to assign (%d).  Try again\n\n" % maximumPercentageAssignable)
        return getPercentage(desc_one, domain, category, maximumPercentageAssignable)
    return percentage



def mapDescriptionToTypeID(descriptions, maximumPercentageAssignable):
    '''
    Given some descriptions, the user dictates what percentage of it should
    be allocated to which combination of domains and categories.

    This function returns a typeID (which is an int representation of a combination of
    category and domain) and percentage of assignment that the descriptions
    should be assigned to.
    '''
    print("There is %i percent left to assign to this categorization" % maximumPercentageAssignable)
    category = chooseCategory(descriptions)
    print(category)
    if category == "ignore": #this entry added to ignore table
        addToIgnore(descriptions)
        return False
    domain = chooseDomain(descriptions)
    if domain == "ignore": #this entry added to ignore table
        addToIgnore(descriptions)
        return False

    assignmentPercentage = getPercentage(descriptions, domain, category, maximumPercentageAssignable)


    #create type if not exists
    typeID = getTypeID(category, domain)
    return typeID, assignmentPercentage
    
    
def getTypeID(category, domain):
    with DBConnection() as dbcnx:
        dbcnx.curs.execute("SELECT id FROM type where domain = '%s' and category = '%s'" % (domain, category))
        typeid = dbcnx.curs.fetchall()
        # print("first pass for typeid yields: {}".format(typeid))
        if (not typeid):
            # print("no typeid found, so attempting insert")
            dbcnx.curs.execute("insert into type (domain, category) values ('%s', '%s')" % (domain, category))
            dbcnx.cnx.commit()
            dbcnx.curs.execute("SELECT id FROM type where domain = '%s' and category = '%s'" % (domain, category))
            typeid = dbcnx.curs.fetchall()
        typeid = typeid[0][0]
        # print("returning typeid {}".format(typeid))
        return typeid

def chooseDomain(descriptions):
    return makeSelection("domain", descriptions)


def chooseCategory(descriptions):
    return makeSelection("category", descriptions)

def showCharIndexes(wholeDesc):
    indexes = ""
    for i in range(len(wholeDesc)):
        indexes += str(i)
        if i > 9:
            indexes += " "
        else:
            indexes += "  "
    print("  ".join(wholeDesc))
    print(indexes)




def getShortenedVersionForTable(wholeDesc):
    '''
        Prompts the user to trim the name of a vendor in order to allow
        other vendors with similar names to be grouped (ie. 'laudrolunge'
        and 'victoria laundrymat') by defining the bounds of the name (in this case 'laundr') 
    '''
    showCharIndexes(wholeDesc)
    #startInd = input("Enter the starting index for the range of characters to add to the {} table.\n Leave blank for 0:  ".format(table))
    startInd = input("Enter the starting index for the range of characters for the trimmed name.\n Leave blank for 0:  ")
    
    # Parse user input
    if startInd == "":
        startInd = 0
    else:
        try:
            startInd = int(startInd)
        except:
            print("\n\n\n\nIllegal number format; prompting again!\n")
            return getShortenedVersionForTable(wholeDesc)

    endInd = input("Enter the inclusive ending index for the range of characters:  ")
    if endInd == "":
        endInd = len(wholeDesc) + 1
    else:
        try:
            endInd = int(endInd) + 1
        except:
            print("\n\n\n\nIllegal number format; prompting again!\n")
            return getShortenedVersionForTable(wholeDesc)
    # print(wholeDesc[startInd:endInd])
    return wholeDesc[startInd:endInd]

def makeSelection(tableName, description):
    allElements = getAllElements(tableName)
    dic = {}
    counter = 1
    print('\nChoose a %s for %s' % (tableName, description))
    for el in allElements:
        dic[str(counter)] = el[0]
        print("%d: %s" % (counter, el[0]))
        counter += 1
    selection = input("Enter number of selection or type the name of a new option [or type 'ignore' to ignore all entries with this description]:\n>")
    print(selection)
    if selection == "ignore":
        # Whole name or just a subset?
        #nameToIgnore = getShortenedVersionForTable(description)
        # This should be a shortened version already....
        print("Are you sure you want to ignore all future instances of '%s'?" % description)#nameToIgnore)
        confirmation = input("y/n: ")
        affirmations = ["y", "yes"]
        if confirmation in affirmations:
            addToIgnore(description)
            return "ignore"
        else:
            print("NOT added to ignore table, let's do this again...\n")
            makeSelection(tableName, description)


    if selection in dic.keys():
        return dic[selection]
    addNameElementToTable(tableName, selection)
    return selection

#https://dev.mysql.com/doc/connector-python/en/connector-python-example-ddl.html

'''
    Returns the assID (primary key) for an assignment and creates it if
    it doesn't exist.
'''
def addToAssignments(description, typeID, percentage):
    with DBConnection() as dbcnx:
        percentage *= .01
        dbcnx.curs.execute("insert into assignment (descr, type, percentage) values ('%s', '%s', '%s')" % (description, typeID, percentage))
        dbcnx.cnx.commit()
        dbcnx.curs.execute("SELECT id FROM assignment where descr = '%s' and type = '%s' and percentage = %s" % (description, typeID, percentage))
        assID = dbcnx.curs.fetchall()[0][0]
        return assID

def getExpenditureID(date, account):
    with DBConnection() as dbcnx:
        dbcnx.curs.execute("SELECT id FROM expenditure where date = '%s' and account = '%s'" % (date, account))
        expendID = dbcnx.curs.fetchall()
        #Scaffolding
        print('finding the expendid')
        print(expendID)
        if not expendID:
            addToExpenditure(date, account)
            return getExpenditureID(date, account)
        return expendID[0][0]

def getInvestmentID(typeID, amount):
    with DBConnection() as dbcnx:
        dbcnx.curs.execute("SELECT id FROM investment where type = '%s' and amount = '%s'" % (typeID, amount))
        investID = dbcnx.curs.fetchall()
        print("adding type   {}    of amount   {}".format(typeID, amount))
        if not investID:
            addToinvestment(typeID, amount)
            return getInvestmentID(typeID, amount)
        return investID[0][0]

def addToinvestment(typeID, amount):
    with DBConnection() as dbcnx:
        print("type:{}    amount:{}".format(typeID, amount))
        dbcnx.curs.execute("insert into investment (type, amount) values ('%s', '%s')" % (typeID, amount))
        dbcnx.cnx.commit()


def addToExpenditure(date, account):
    with DBConnection() as dbcnx:
        dbcnx.curs.execute("insert into expenditure (date, account) values ('%s', '%s')" % (date, account))
        dbcnx.cnx.commit()



def addToTransaction(expenditure, investment):
    with DBConnection() as dbcnx:
        dbcnx.curs.execute("insert into transaction (expenditure, investment) values ('%s', '%s')" % (expenditure, investment))
        dbcnx.cnx.commit()


def reformatDate(date):
    #example date format from CSV file "8/28/2018"
    #date format required for mysql: YYYY-MM-DD

    d = date.split("/")
    dout = d[2] + "-"
    month = d[0]
    if len(month) < 2:
        month = "0" + month
    dout += month + "-"

    day = d[1]
    if len(day) < 2:
        day = "0" + day
    dout += day

    return dout


def returnAllElementsInTable(table):
    '''
        fetches all elements from a table and returns
        as a list for further processing.
    '''
    with DBConnection() as dbcnx:
        try:
            dbcnx.cursor.execute("SELECT * FROM {}".format(table))
            results = dbcnx.cursor.fetchall()
            return results
        except mysql.connector.Error as err:
            print("Database error!")
            print(err)
            if err.errno == 1146:
                print("Table does not exist!")
                return None


def getInvestmentSummary():
    '''
        Returns a list summarizing the totals spend within each type of investment.

        This is the full MySQL query:
        select t.category as Category, t.domain as Domain, sum(i.amount) as totalSpent from type t, investment i where t.id = i.type group by i.type;
    '''
    with DBConnection() as dbcnx:
        try:
            totalLabel = "totalSpent"
            criteria = "t.category AS Category, t.domain AS Domain, SUM(i.amount) AS " + totalLabel
            tables = "type t, investment i"
            clause = "t.id = i.type"
            grouping = "i.type"
            ordering = totalLabel + " DESC"
            queryString = "SELECT {} FROM {} WHERE {} GROUP BY {} ORDER BY {}".format(
                criteria, tables, clause, grouping, ordering
            )
            dbcnx.cursor.execute(queryString)
            results = dbcnx.cursor.fetchall()
            return results
        except mysql.connector.Error as err:
            print("Database error!")
            print(err)
            return None
            # if err.errno == 1146:
            #     print("Table does not exist!")
            #     return None    
