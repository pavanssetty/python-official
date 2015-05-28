#!/usr/bin/python
from P4 import P4,P4Exception
import shutil, os
import time
import traceback
import csv
import sys


outputlog = open("creation_log-"+time.strftime("%d-%m-%Y")+".log" , 'a+')
changelistlog = open("change_log-"+time.strftime("%d-%m-%Y")+".log" , 'a+')
p4 = P4()
p4.port="perforce:1666"
p4.user = "username" # to be changed to the tester's id
p4.password = 'password'
p4.client = "clientdev" # Create a workspace with workspace root mapped to the depot root where you want to checkin the migrated content
#workspaceRoot = '/depotdata/p4admin_deheremap6382'  # Local diskspace where you want to create the workspace.
#p4.debug=3
p4.connect()
p4.run_login()
outputlog.writelines("***************************************Script Started********************************")
outputlog.writelines(time.ctime()+ "    PROD Client Connected\n")
changelistlog.writelines(time.ctime()+ "    PROD Run time \n")
sharelocation_list_csv_file = 'ShareLocations_Mapping_list.csv'
locationList = []
specialCharacterFiles = []

try:
    with open(sharelocation_list_csv_file) as csv_file_read:
        reader = csv.DictReader(csv_file_read)
        locationList = [row for row in reader]
except (FileNotFoundError, IOError):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    outputlog.writelines(time.ctime()+ "    " + exc_value + "************EXIT****************")
    exit(0)
#csv_file_read = csv.DictReader(open(sharelocation_list_csv_file,'r'), delimiter='|', quotechar='"')

for iterator in range(len(locationList)):

    try:
        client_variable = p4.fetch_client()
        client_variable._root = locationList[iterator]['WorkspaceRoot']
        outputlog.writelines(time.ctime()+"  Picking up Root as "+ locationList[iterator]['WorkspaceRoot']+" to reconcile with  /"+locationList[iterator]['DepotLocation'] + "\n")
        p4.save_client(client_variable)

        try:
            print("To checkin files")
            reconcile_variable = p4.run_reconcile('-f','/'+locationList[iterator]['DepotLocation']+'/...')
            outputlog.writelines(time.ctime()+"    Reconcile Completed "+locationList[iterator]['WorkspaceRoot']+" to   "+locationList[iterator]['DepotLocation'] + "\n")
            print("*********************reconcile done*****************************\n")
            #print(reconcile_variable)
        except P4Exception:
            outputlog.writelines("******************EXCEPTION DURING RECONCILE**********************************\n")
            locationList[iterator]['Result'] = 'Reconcile Failed'
            continue
            
        change = p4.fetch_change()
        change._description = time.ctime()+"    "+locationList[iterator]['WorkspaceRoot']+"    "+locationList[iterator]['DepotLocation']


        # Remove special Character files from changelist files
        # while i < len(change['Files']):
        #     if ('&' in change['Files'][i]) or ('%' in change['Files'][i]):
        #         p4.run("revert", "-k",change['Files'][i]) 
        #         change = p4.fetch_change() #a.pop(i)
        #         i = 0
        #     else:
        #         i+=1

        # for i in range(len(change['Files'])):
        #     if ('&' in change['Files'][i]) or ('%' in change['Files'][i]):
        #         p4.run("revert", "-k",change['Files'][i])
        for filename in change['Files']:
            if ('%' in filename) or ('&' in filename):
                p4.run("revert", "-k",filename)
                outputlog.writelines("Special Character filename found " + filename +" while submitting at \\"+ locationList[iterator]['DepotLocation'] )
                specialCharacterFiles.append(filename)

        change = p4.fetch_change()
        submit = p4.run_submit(change)
        locationList[iterator]['Result'] = 'Success'

        outputlog.writelines(time.ctime()+"    " + "Submitted share location "+ locationList[iterator]['WorkspaceRoot'] +" to changelist number "+ submit[0]['change']+ "\n")
        changelistlog.writelines(time.ctime()+"    "+ submit[0]['change']+ " \n")

    except P4Exception:
        outputlog.writelines("******************EXCEPTION***********************************\n")
        outputlog.writelines("Error while submitting changelist with " + locationList[iterator]['DepotLocation'] )
        locationList[iterator]['Result'] = 'Submit Failed'

        traceback.print_exc(file=sys.stdout)

outputlog.writelines("Failed Locations in the run: \n")
for iterator in range(len(locationList)):
    if not 'Success' in  locationList[iterator]['Result']:
        outputlog.writelines('*) '+locationList[iterator]['DepotLocation'] +"Result: "+ locationList[iterator]['Result'])

outputlog.writelines("Special Character Files list. Kindly rename them before next run.")   
for item in specialCharacterFiles:
    outputlog.writelines('*) '+ item)
    
