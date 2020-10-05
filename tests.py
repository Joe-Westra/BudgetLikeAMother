#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  tests.py
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

import unittest
import mysql.connector
import re
from dbconnector import *

class Test_dbconnector(unittest.TestCase):


    # conn = getConnectionToMySQL()
    # curs = getCursorFromConnection(conn)
    # cursindb = enterBudgetDB(curs)


    def test_connectToMySQL(self):
        with DBConnection() as dbcnx:
            cnx = dbcnx.cnx
            self.assertIsInstance(cnx, mysql.connector.connection.MySQLConnection)


    def test_getCursorFromConnection(self):
        '''
            Will fail if the database does not exist with the following:
                    Database BUDGET does not exist.
                    1049 (42000): Unknown database 'BUDGET'
        '''
        with DBConnection() as dbcnx:
            curs = dbcnx.curs
            self.assertIsInstance(curs, mysql.connector.cursor.MySQLCursor)

    def test_enterBudgetDB(self):
        with DBConnection() as dbcnx:
            dbcnx.curs.execute("SHOW DATABASES")
            # show databases returns a tuple where the second element in the array
            # contains the db name...
            db = dbcnx.curs.fetchall()[1]
            # ...as the first element...
            self.assertEqual(db[0], "BUDGET")
            

    # def test_dropTables(self):
    # '''
    #     Tests the function that clears out unwanted tables...
    # '''
    #     with DBConnection() as dbcnx:
    #         self.assertTrue(dropTables(curs))
    
    
    def test_createTables(self):
        '''
            Attempt to create all tables.  Use this after testing dropTables
            if you want to start from a clean database
        '''
        with DBConnection() as dbcnx:
            try:
                # The tables might already exist, if so this will throw an error
                cursor = createTables()
            except mysql.connector.Error as err:
                print(err)
            dbcnx.cursor.execute("SHOW TABLES")
            tables = dbcnx.cursor.fetchall()
            sqlTableList = ['assignment','category','description','domain','investment','transaction','type', 'expenditure', 'descs_to_ignore']
            for name in tables:
                self.assertTrue(name[0] in sqlTableList)
    

    def test_addToDomain(self):
        t = "test"
        with DBConnection() as dbcnx:
            dbcnx.cursor.execute("SHOW TABLES")
            tables = dbcnx.cursor.fetchall()
            print("TABLES    : " + str(tables))
            
            
            try:
                # The test phrase mgiht already be in the domain table...
                addToDomain(t)
            except mysql.connector.Error as err:
                print(err)
            dbcnx.cursor.execute("SELECT * FROM domain WHERE name = '{}'".format(t))
            tables = dbcnx.cursor.fetchall()
            print(tables)
            self.assertFalse(tables == [])

            #clean up
            dbcnx.cursor.execute("DELETE FROM domain WHERE name = '{}'".format(t))



    def test_addNameElementToTable(self):
        '''
            Tests the more flexible version of the above method called.
        '''
        with DBConnection() as dbcnx:
            table = "domain"
            name = "test"
            # self.assertTrue(addNameElementToTable(table, name))
            try:
                addNameElementToTable(table, name)
            except mysql.connector.Error as err:
                print("Is {} already entered in {} table?".format(name, test))
                print(err)
            
            dbcnx.cursor.execute("SELECT * FROM %s WHERE name = '%s'" % (table, name))
            instances = dbcnx.cursor.fetchall()
            print(instances)
            self.assertFalse(instances == [])
        
            #clean up
            dbcnx.cursor.execute("DELETE FROM %s WHERE name = '%s'" % (table, name))
        

    
    def test_isInDescTable(self):
        with DBConnection() as dbcnx:
            # test where element does not exist
            desc = "some_made_up_description"
            self.assertFalse(elementIsInDescriptionTable(desc))
        
            table = "description"
            name = "test test"
        
            # test where element does exist
            addNameElementToTable(table, name)
            self.assertTrue(elementIsInDescriptionTable(name))

            #clean up
            dbcnx.cursor.execute("DELETE FROM %s WHERE name = '%s'" % (table, name))
        


if __name__ == '__main__':
    unittest.main()
