import datetime
import serial
from pip._vendor.distlib.compat import raw_input
from pymongo import MongoClient
from bson.objectid import ObjectId
client = MongoClient('mongodb://localhost:27000')

db = client.rasp13
#PortRF = serial.Serial('/dev/ttyAMA0', 9600)

toulouseLocId = ObjectId('5e12fe5ef6b9e2ba7f060b71') #toulouse


def chooseLocation(inputMsg):
    locTempId = 0
    locIdArray = []
    myLocs = db.locations.find()
    for doc in myLocs:
        print('ID: ' + str(locTempId) + ' :' + str(doc))
        locIdArray.append(doc['_id'])
        locTempId = locTempId + 1

    custLocId = str(raw_input(inputMsg))
    return locIdArray[int(custLocId)]


def chooseCustomer(inputMsg):
    custTempId = 0
    custIdArray = []
    myCust = db.customers.find()
    for doc in myCust:
        print('ID: ' + str(custTempId) + ' :' + str(doc))
        custIdArray.append(doc['_id'])
        custTempId = custTempId + 1

    custLocId = str(raw_input(inputMsg))
    return custIdArray[int(custLocId)]


def readRFID():
    print("Running RFID Reader...")
    """""
    ID = ""
    while len(ID) < 12:
        read_byte = PortRF.read()
        if read_byte == "\x02":
            for Counter in range(0, 12):
                read_byte = PortRF.read()
                ID = ID + str(read_byte)
    return ID
    """""
    return '00EBBR0882EE'
print("List of Commands: GetAllLocations, InsertLocation, InsertCustomer, CreateParcel, ParcelHistory, RfidReader, UpdateParcelStatus")
command = str(raw_input('Please enter a command:'))

if command == 'GetAllLocations':
    myLocs = db.locations.find()
    for doc in myLocs:
        print(doc)

elif command == 'InsertLocation':
    locAdd = str(raw_input('Please enter an address:'))
    locCity = str(raw_input('Please enter a city:'))
    res = db.locations.insert_one({'locAddress': str(locAdd), 'city': str(locCity)})
    if res.acknowledged == True:
        print('You have successfully entered a new address')
    else:
        print('Error inserting a new address')

elif command == 'InsertCustomer':
    custName = str(raw_input('Please enter a customer name:'))
    homeLoc = chooseLocation('Please enter a home location from the ID above: ')
    res = db.customers.insert_one({'custName': str(custName), 'homeLocation': homeLoc})

    if res.acknowledged == True:
        print('You have successfully entered a new address')
    else:
        print('Error inserting a new address')

elif command == 'CreateParcel':
    pWt = str(raw_input('Please enter a parcel weight:'))
    cust = chooseCustomer('Please choose a customer by entering an ID: ')
    boardLoc = db.customers.find_one({"_id": cust}, {"homeLocation": 1, "_id": 0})
    destLoc = chooseLocation('Please enter a destination location from the ID above: ')
    newOp = {"date": datetime.datetime.now(), "location": boardLoc["homeLocation"], "operation": "boarding"}
    newParcel  = {"parcels": {"_id": ObjectId(), 'weight': pWt, 'destLocation': destLoc, 'operations':[newOp] } }
    res = db.customers.update_one({"_id": cust}, {"$push": newParcel})

    if res.acknowledged == True:
        print('You have successfully entered a new parcel')
    else:
        print('Error inserting a new address')

elif command == 'ParcelHistory':
    pHisCom = str(raw_input("Do you want to view all history (ViewAll) or for a specific customer (Customer):"))

    if pHisCom == "ViewAll":
        parcels = db.customers.find({"parcels": {"$exists": True, "$ne": "null"}}, {"parcels": 1, "_id": 0})
        for doc in parcels:
            print(doc)
    elif pHisCom == "Customer":
        cust = chooseCustomer("Select a customer from the list to see their parcel history:")
        parcels = db.customers.find({"_id": cust}, {"parcels": 1, "_id": 0})
        for doc in parcels:
            print(doc)
    else:
        print("Error: Unknown Command")

elif command.upper() == "UPDATEPARCELSTATUS":
    idx = 1;
    parcelLst = []
    parcels = db.customers.find({"parcels": {"$exists": True, "$ne": "null"}}, {"parcels": 1, "_id": 0})
    for doc in parcels:
        for d in doc['parcels']:
            print("Parcel : " + str(idx) + " :", d)
            parcelLst.append(d)
            idx = idx + 1

    updateParcelCmd = int(raw_input("Please enter a ID of the parcel you want to update: "))
    print("You are updating parcel : " + str(parcelLst[(updateParcelCmd - 1)]))
    updateParcelStatusCmd = str(raw_input("Please input the status you want to enter for this parcel (Transfer, FinalLocation): "))
    parcelLoc = chooseLocation("Please choose the location for the operation:")
    packID = parcelLst[updateParcelCmd - 1]['_id']
    print("package ID = ", packID)
    if(updateParcelStatusCmd.upper() == 'TRANSFER'):
        newOp = {"date": datetime.datetime.now(), "location": parcelLoc, "operation": "transfer"}
        res = db.customers.update_one({"parcels._id": ObjectId(packID)}, {"$push": {"parcels.$.operations": newOp}})

        if res.acknowledged == True:
            print("Package Transfer Successful")
        else:
            print("There was an error updating your package transfer")

    elif updateParcelStatusCmd.upper() == 'FINALLOCATION':
        newOp = {"date": datetime.datetime.now(), "location": parcelLoc, "operation": "deliverd"}
        res = db.customers.update_one({"parcels._id": packID}, {"$push": {"parcels.$.operations": newOp}})
        if res.acknowledged == True:
            print("Package Delivered Successful")
        else:
            print("There was an error updating your package transfer")
            
    else:
        print("Command Unknown")

elif command.upper() == "RFIDREADER":
    print("Waiting to Read package ID")
    packID = readRFID()
    print("Successful Package ID Read: ", packID)
    parcelDoc = []
    #check if parcel exists
    parcel = db.customers.find({"parcels": {"$elemMatch": {"_id": packID}}}, {"parcels": 1, "_id":0});
    for p in parcel:
        parcelDoc.append(p)

    if len(parcelDoc) > 0:
        #parcel exists
        print("Adding new transfer at location Toulouse")
        newOp = {"date": datetime.datetime.now(), "location": toulouseLocId, "operation": "transfer"}
        res = db.customers.update_one({"parcels._id": ObjectId(packID)}, {"$push": {"parcels.$.operations": newOp}})

    elif len(parcelDoc) == 0:
        cust = chooseCustomer("This parcel is new. Please select a customer to ship this package:")
        pWt = str(raw_input('Please enter a parcel weight:'))
        boardLoc = db.customers.find_one({"_id": cust}, {"homeLocation": 1, "_id": 0})
        destLoc = chooseLocation('Please enter a destination location from the ID above: ')
        newOp = {"date": datetime.datetime.now(), "location": boardLoc, "operation": "boarding"}
        newParcel = {"parcels": [{"_id": packID, 'weight': pWt, 'destLocation': destLoc, 'operations': [newOp]}]}
        res = db.customers.update_one({"_id": cust}, {"$set": newParcel})
        
    else:
        print("Error retrieving packages")


else:
    print('Unknown Command')