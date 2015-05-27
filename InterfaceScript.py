#!/usr/bin/python
from P4 import P4,P4Exception
import shutil, os
import time
import traceback
import csv
import sys


outputlog = open("creation_log.log" , 'a+')
changelistlog = open("change_log.log" , 'a+')
p4 = P4()
p4.port="perforce:1666"
p4.user = "username" # to be changed to the tester's id
p4.password = 'password'
p4.client = "hydhtc82865l_dev" # Create a workspace with workspace root mapped to the depot root where you want to checkin the migrated content
#workspaceRoot = '/depotdata/p4admin_deheremap6382'  # Local diskspace where you want to create the workspace.
p4.debug=3
p4.connect()
p4.run_login()
outputlog.writelines(time.ctime()+ "    PROD Client Connected\n")
changelistlog.writelines(time.ctime()+ "    PROD Run time \n")
sharelocation_list_csv_file = 'ShareLocations_Mapping_list.csv'

with open(sharelocation_list_csv_file) as csv_file_read:
    reader = csv.DictReader(csv_file_read)
    locationList = [row for row in reader]

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

        submit = p4.run_submit(change)
        locationList[iterator]['Result'] = 'Success'

        outputlog.writelines(time.ctime()+"    " + "Submitted share location "+ locationList[iterator]['WorkspaceRoot'] +" to changelist number "+ submit[0]['change']+ "\n")
        changelistlog.writelines(time.ctime()+"    "+ submit[0]['change']+ " \n")

    except P4Exception:
        outputlog.writelines("******************EXCEPTION***********************************\n")
        outputlog.writelines("Error while submitting changelist with " + locationList[iterator]['DepotLocation'] + " Check Log file\n")
        locationList[iterator]['Result'] = 'Submit Failed'

        traceback.print_exc(file=sys.stdout)
    # except Exception:
    #     outputlog.writelines("*********************EXCEPTION********************************\n")
    #     outputlog.writelines("Error in copying data. Check Log file\n")
    #     traceback.print_exc(file=sys.stdout)
