#!/usr/bin/python
from P4 import P4,P4Exception
import os
import time
import traceback
import csv
import sys


outputlog = open("creation_log-"+time.strftime("%d%m%Y")+".log" , 'a+')
changelistlog = open("change_log-"+time.strftime("%d%m%Y")+".log" , 'a+')
p4 = P4()
p4.port="ipaddress:1666"
p4.user = "username" # to be changed to the tester's id
p4.password = 'password'
p4.client = "hydhtc82865l_dev" # Create a workspace with workspace root mapped to the depot root where you want to checkin the migrated content
#workspaceRoot = '/depotdata/p4admin_deheremap6382'  # Local diskspace where you want to create the workspace.
#p4.debug=3
p4.connect()
p4.run_login()
outputlog.writelines(time.ctime()+ "***************************************Script Started********************************\n")
outputlog.writelines("\n"+ time.ctime()+ "    PROD Client Connected\n")
changelistlog.writelines(time.ctime()+ "    PROD Run Start \n")
sharelocation_list_csv_file = 'ShareLocations_Mapping_list.csv'
locationList = []
specialCharacterFiles = []
specialCharacterFileFlag = 0

try: #if csv file is not present, then the script will terminate. We need not raise RFC to remove from crontab :)
    with open(sharelocation_list_csv_file) as csv_file_read:
        reader = csv.DictReader(csv_file_read)
        locationList = [row for row in reader]
except (FileNotFoundError, IOError):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    outputlog.writelines(time.ctime()+ "    " + str(exc_value) + "************EXIT****************\n")
    print(exc_value)
    exit(1)
#csv_file_read = csv.DictReader(open(sharelocation_list_csv_file,'r'), delimiter='|', quotechar='"')

for iterator in range(len(locationList)):

    try:
        retry = 0
        while retry < 3:
            if not os.path.exists(locationList[iterator]['WorkspaceRoot']):
                retry += 1
                print("Retry attempt: " + str(retry))
                time.sleep(5)
                continue
            else:
                retry = 5
                break
        print("Retry variable value " + str(retry))        
        if retry == 5:
            client_variable = p4.fetch_client()
            client_variable._root = locationList[iterator]['WorkspaceRoot']
            outputlog.writelines(time.ctime()+"  Picking up Root as "+ locationList[iterator]['WorkspaceRoot']+" to reconcile with  /"+locationList[iterator]['DepotLocation'] + "\n")
            p4.save_client(client_variable)
            try:
                reconcile_variable = p4.run_reconcile('-f','/'+locationList[iterator]['DepotLocation']+'/...')
                outputlog.writelines(time.ctime()+"    Reconcile Completed "+locationList[iterator]['WorkspaceRoot']+" to   "+locationList[iterator]['DepotLocation'] + "\n")
                #print(reconcile_variable)

                #retry = 3
            except P4Exception:
                outputlog.writelines(time.ctime()+ "******************EXCEPTION DURING RECONCILE**********************************\n")
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print(exc_value)
                outputlog.writelines(time.ctime()+ "    " + str(exc_value) + "\n")
                locationList[iterator]['Result'] = 'Reconcile Failed or No files to reconcile'
                #retry = 5
                continue #break
            change = p4.fetch_change()
            change._description = time.ctime()+"    "+locationList[iterator]['WorkspaceRoot']+"    "+locationList[iterator]['DepotLocation']


            for filename in change['Files']:
                if ('%' in filename) or ('&' in filename) or ('@' in filename) or ('*' in filename) or ('#' in filename):
                    specialCharacterFileFlag = 1
                    p4.run("revert", "-k",filename)
                    outputlog.writelines(time.ctime()+ "Special Character filename found " + filename +" while submitting at \\"+ locationList[iterator]['DepotLocation'] +"\n")
                    specialCharacterFiles.append(filename)

            change = p4.fetch_change()
            change._description = time.ctime()+"    "+locationList[iterator]['WorkspaceRoot']+"    "+locationList[iterator]['DepotLocation']
            submit = p4.run_submit(change)
            locationList[iterator]['Result'] = 'Success'

            outputlog.writelines(time.ctime()+"    " + "Submitted share location "+ locationList[iterator]['WorkspaceRoot'] +" to changelist number "+ submit[0]['change']+ "\n")
            changelistlog.writelines(time.ctime()+"    "+ submit[0]['change']+ " \n")
        else:
            locationList[iterator]['Result'] = locationList[iterator]['WorkspaceRoot'] +'  Location not accessible'

    except P4Exception:
        outputlog.writelines(time.ctime()+ "******************EXCEPTION***********************************\n")
        outputlog.writelines(time.ctime()+ "Error while submitting changelist with " + locationList[iterator]['DepotLocation'] +"\n")
        locationList[iterator]['Result'] = 'Submit Failed'
        #p4.run("revert", "-k",'/'+locationList[iterator]['DepotLocation']+'/...')

        traceback.print_exc(file=sys.stdout)

outputlog.writelines(time.ctime()+ "Failed Locations in the run: \n")
for iterator in range(len(locationList)):
    if not 'Success' in  locationList[iterator]['Result']:
        outputlog.writelines('*) '+locationList[iterator]['DepotLocation'] +"Result: "+ locationList[iterator]['Result']+"\n")
        print('*) '+locationList[iterator]['DepotLocation'] +"      Result: "+ locationList[iterator]['Result'] +"\n")

if specialCharacterFileFlag == 1:
    outputlog.writelines(time.ctime()+ "Special Character Files list. Kindly rename them before next run.\n")   
    for item in specialCharacterFiles:
        outputlog.writelines('*) '+ item+"\n")
        print('*) '+ item)    
