import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId
client = MongoClient('mongodb://localhost:27000')

db = client.rasp13

def chooseLocation(inputMsg):
    locTempId = 0
    locIdArray = []
    myLocs = db.locations.find()
    for doc in myLocs:
        print('ID: ' + str(locTempId) + ' :' + str(doc))
        locIdArray.append(doc['_id'])
        locTempId = locTempId + 1

    custLocId = input(inputMsg)
    return locIdArray[int(custLocId)]

def chooseCustomer(inputMsg):
    custTempId = 0
    custIdArray = []
    myCust = db.customers.find()
    for doc in myCust:
        print('ID: ' + str(custTempId) + ' :' + str(doc))
        custIdArray.append(doc['_id'])
        custTempId = custTempId + 1

    custLocId = input(inputMsg)
    return custIdArray[int(custLocId)]

print("List of Commands: GetAllLocations, InsertLocation, InsertCustomer, CreateParcel, ParcelHistory")
command = input('Please enter a command:')

if command == 'GetAllLocations':
    myLocs = db.locations.find()
    for doc in myLocs:
        print(doc)

elif command == 'InsertLocation':
    locAdd = input('Please enter an address:')
    locCity = input('Please enter a city:')
    res = db.locations.insert_one({'locAddress': str(locAdd), 'city': str(locCity)})
    if res.acknowledged == True:
        print('You have successfully entered a new address')
    else:
        print('Error inserting a new address')

elif command == 'InsertCustomer':
    custName = input('Please enter a customer name:')
    homeLoc = chooseLocation('Please enter a home location from the ID above: ')
    res = db.customers.insert_one({'custName': str(custName), 'homeLocation': homeLoc})

    if res.acknowledged == True:
        print('You have successfully entered a new address')
    else:
        print('Error inserting a new address')

elif command == 'CreateParcel':
    pWt = input('Please enter a parcel weight:')
    cust = chooseCustomer('Please choose a customer by entering an ID: ')
    boardLoc = db.customers.find_one({"_id": cust}, {"homeLocation": 1})
    destLoc = chooseLocation('Please enter a destination location from the ID above: ')
    newOp = {"date": datetime.datetime.now(), "location": boardLoc, "operation": "boarding"}
    newParcel  = {"parcels": [{"_id": ObjectId(), 'weight': pWt, 'destLocation': destLoc, 'operations':[newOp] }]  }
    res = db.customers.update_one({"_id": cust}, {"$set": newParcel})

    if res.acknowledged == True:
        print('You have successfully entered a new parcel')
    else:
        print('Error inserting a new address')

elif command == 'ParcelHistory':
    pHisCom = input("Do you want to view all history (ViewAll) or for a specific customer (Customer):")

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

else:
    print('Unknown Command')