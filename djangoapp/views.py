from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import pymongo
from django.http import JsonResponse
from django.core import serializers
import json
import datetime
import calendar
import time
import datetime
from datetime import timezone
import threading
from pymongo import ReturnDocument

# import moment


client = pymongo.MongoClient('mongodb://localhost:27017')
dbname = client['djangop']

PROJECT_TYPE = "AQMS"
hubResponse = {"status": "ok", "errorCode": 0, "message": "None"}
errorResponse = {"status": 'error', "errorCode": -1, "message": "failed"}

NEED_AQI = True


@csrf_exempt
def addSensor(request):
    if request.method == "POST":
        sensor_data = json.loads(request.body)
        isParamNameExists = False
        collection = dbname['sensor_parameter']
        if collection.find_one({"paramName": sensor_data["paramName"]}):
            errorResponse["message"] = 'Sensor already exists'
            return JsonResponse(errorResponse, safe=False)
        else:
            inserted_data = collection.insert_one(sensor_data)
            return JsonResponse(hubResponse, safe=False)


def getSensor(request):
    collection = dbname['sensor_parameter']
    sensorData = []
    isQuery = False
    if request.GET:
        sensorQuery = request.GET["paramName"]
        sensor_data = collection.find_one({"paramName": {"$regex": sensorQuery}}, {"_id": False})
        sensorData.append(sensor_data)


    else:
        for x in collection.find({}, {'_id': False}):
            sensorData.append(x)

    hubResponse["data"] = sensorData
    return JsonResponse(hubResponse, safe=False)


@csrf_exempt
def adddevices(request):
    if request.method == "POST":
        response = None
        device_data = json.loads(request.body)
        if device_data != None:
            response = registerDevice(device_data)
            if response == "success":
                return JsonResponse(hubResponse, safe=False)
            else:
                return JsonResponse(errorResponse, safe=False)


@csrf_exempt
def getdevice(request):
    data = []
    if request.method == 'GET':
        database = dbname["djangop"]
        try:
            collection = dbname["devices"]
            data = collection.find({}, {'_id': 0})
            hubResponse["message"] = data
            return HttpResponse(data, hubResponse)
        except:
            return HttpResponse(errorResponse)


@csrf_exempt
def addDeviceFamily(request):
    if request.method == "POST":
        data = json.loads(request.body)
        collection = dbname['Sensor_Types']
        isSubtypeExists = collection.find_one({'subType': data['subType']})
        isTypeExists = collection.find_one({'Type': data['Type']})

        deviceFamilyModel = {
            "subType": None,
            "Type": None,
            "deviceFamily": [],
        }
        deviceFamily = []
        if isSubtypeExists and isTypeExists != None:
            isSensorExists = dbname["sensor_parameter"].find_one({"paramName": data["deviceFamily"]})
            isFamilyAlreadyAdded = collection.find_one({"deviceFamily": data["deviceFamily"]})

            if isSensorExists and isFamilyAlreadyAdded == None:
                collection.update_one({'subType': data['subType']}, {'$push': {'deviceFamily': data['deviceFamily']}})
                return (hubResponse)
            elif isFamilyAlreadyAdded != None:
                errorResponse["message"] = 'Device Family already added'
                return JsonResponse(errorResponse, safe=False)
            else:
                errorResponse["message"] = 'No sensor existing with this name'
                return JsonResponse(errorResponse, safe=False)
        else:
            isSensorExists = dbname["sensor_parameter"].find_one({"paramName": data["deviceFamily"]})
            if isSensorExists:
                deviceFamilyModel["subType"] = data['subType']
                deviceFamilyModel["Type"] = data['Type']
                deviceFamilyModel["deviceFamily"].append(data['deviceFamily'])
                collection.insert_one(deviceFamilyModel)
                return JsonResponse(hubResponse, safe=False)
            else:
                errorResponse["message"] = 'No sensor existing with this name'
                return JsonResponse(errorResponse, safe=False)
    elif request.method == "GET":
        i = 0
        data = []
        if request.GET:
            paramNameQuery = request.GET["paramName"]
            result = dbname["Sensor_Types"].find_one({"subType": {"$regex": paramNameQuery}}, {"_id": False})
            data.append(result)
        else:
            deviceTypes = None
            for x in dbname["Sensor_Types"].find({}, {'_id': 0}):
                data.append(x)
        hubResponse["data"] = data

        return JsonResponse(hubResponse, safe=False)


@csrf_exempt
def getDeviceFamily(request):
    data = []
    if request.GET:
        subTypeQuery = request.GET["subType"]
        result = dbname["Sensor_Types"].find_one({"subType": {"$regex": subTypeQuery}}, {"_id": False})
        data.append(result)
    else:
        deviceTypes = None
        for x in dbname["Sensor_Types"].find({}, {'_id': 0}):
            data.append(x)
    hubResponse["data"] = data

    return JsonResponse(hubResponse, safe=False)


@csrf_exempt
def processLiveData(request):
    if request.method == "POST":
        hubResponse = {"status": "ok", "errorCode": 0, "message": "None", "data": "None"}
        received_json_data = json.loads(request.body)
        dataOfRequest = {}
        processed_data = None
        if received_json_data != None:
            data = received_json_data["data"]
            data["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data["status"] = "ready"
        if PROJECT_TYPE == "AQMS":
            processed_data = getAqmsConversion(data)
            aqi = updateStatusAQI(data["time"], received_json_data["deviceId"])

        result = pushSensorData(received_json_data["deviceId"], processed_data)
        processIncomingData()
        if result == "success":
            return JsonResponse(hubResponse, safe=False)
        else:
            return JsonResponse(errorResponse, safe=False)


def getStatCollectionPrefixFromDeviceLogicalId(logicalId):
    return logicalId + "_stat"


def findOneAndUpdate(collection_name, query, jsonData, sortOption):
    collection = dbname[collection_name]
    test = collection.find_one()

    received_data = collection.find_one_and_update(query, {'$set': jsonData}, {'sort': sortOption})
    return received_data


def processIncomingData():
    incomming_data = findOneAndUpdate("device_raw_data", {"status": "ready"}, {"status": "processing"},
                                      {"data.receivedTime": 1})

    collection = dbname['device_raw_data']
    result = collection.find_one(incomming_data)
    pushItem = result
    sensorId = result["deviceId"]
    deviceId = result["deviceId"]
    data = pushItem["data"]

    device = getDeviceFromId(deviceId)
    if device != None and device["logicalDeviceId"] != None:
        collectionName = device["logicalDeviceId"]
        proccessed_data = ProcessSensorData(data)

        epoch_time = data["receivedTime"]
        current_date = datetime.datetime.now()

        date_time = datetime.datetime.fromtimestamp(epoch_time)  # converting epoch to current date time

        if proccessed_data != None:
            filteredData = {
                "deviceId": sensorId,
                "logicalDeviceId": device["logicalDeviceId"],
                "data": proccessed_data
            }
            collection = dbname[collectionName]
            collection.insert_one(filteredData)
            collectionNamePrefix = getStatCollectionPrefixFromDeviceLogicalId(device["logicalDeviceId"])

            updateStatistics(epoch_time, collectionNamePrefix, proccessed_data, device)


def updateStatistics(date, collectionNamePrefix, dataObj, device):
    paramNameList = []
    for propFieldItem in dataObj:
        if propFieldItem != 'GPS':
            paramNameList.append(propFieldItem)

    def updateStatItem():
        for x in range(len(paramNameList)):
            propField = paramNameList[x]
            updateHourlyStats(collectionNamePrefix + "_hourly", propField, dataObj[propField], date, dataObj)
            updateDailyStats(collectionNamePrefix + "_daily", propField, dataObj[propField], date, dataObj)

    updateStatItem()


def updateDailyStats(collectionName, paramName, value, currentDate, dataob):
    if collectionName != None and currentDate != None and paramName != None:
        key = dateToDailyUsageKey(currentDate, None)
        deviceQuery = {
            "paramName": {'$in': [paramName]},
            "key": dateToDailyUsageKey(currentDate, None)
        }
        newCollectionItem = None

        dateToHourly = dateToHourlyUsageKey(currentDate, None)

        if paramName == 'windSpeedAvg':
            newCollectionItem = createNewWindStatCollection(paramName, value, currentDate, dateToHourly)
        else:
            newCollectionItem = createNewStatCollection(paramName, value, currentDate, key)

        collection = dbname[collectionName]
        collection.insert_one(newCollectionItem)  # IMP


def updateHourlyStats(collectionName, paramName, value, currentDate, dataob):
    if collectionName != None and currentDate != None and paramName != None:
        deviceQuery = {
            "paramName": {'$in': [paramName]},
            "key": dateToHourlyUsageKey(currentDate, None)
        }
        newCollectionItem = None

        dateToHourly = dateToHourlyUsageKey(currentDate, None)

        if paramName == 'windSpeedAvg':
            newCollectionItem = createNewWindStatCollection(paramName, value, currentDate, dateToHourly)
        else:
            newCollectionItem = createNewStatCollection(paramName, value, currentDate, dateToHourly)

        collection = dbname[collectionName]
        collection.insert_one(newCollectionItem)


def dateToDailyUsageKey(currentDate, timeZoneName):
    date_time = datetime.datetime.fromtimestamp(currentDate)
    date = date_time.strftime("%d")
    month = date_time.strftime("%m")
    year = date_time.strftime("%Y")
    result = date + '.' + month + '.' + year
    return result


def createNewWindStatCollection(paramName, value, currentDate, key):
    print('createNewWindStatCollection')


def createNewStatCollection(paramName, value, currentDate, key):
    newDoc = {
        "paramName": paramName,
        "epoch": currentDate,
        "key": key,
        "statParams": {
            "sum": '',
            "count": '',
            "min": '',
            "max": '',
            "latestValue": ''
        }
    }

    sumVal = None
    minVal = None
    maxVal = None
    latestValue = None

    if value != None:
        newDoc["statParams"]["sum"] = value if paramName == 'prominentPollutant' else float(value)
        newDoc["statParams"]["count"] = 1
        newDoc["statParams"]["min"] = value if paramName == 'prominentPollutant' else int(value)
        newDoc["statParams"]["max"] = value if paramName == 'prominentPollutant' else int(value)
        newDoc["statParams"]["latestValue"] = value if paramName == 'prominentPollutant' else int(value)

    return newDoc


def dateToHourlyUsageKey(dateObj, timeZoneName):
    key = dateObj
    return key


def ProcessSensorData(currentData):
    filterResult = {}
    testObj = {}
    paramDefs = getParamDefinitions()
    paramList = []
    for i in range(len(paramDefs)):
        paramList.append(paramDefs[i]["paramName"])

    for params in currentData:
        if params in paramList:
            filterResult["temperature"] = currentData["temperature"]
            filterResult["pressure"] = currentData["pressure"]
            filterResult["humidity"] = currentData["humidity"]
            filterResult["PM10"] = currentData["PM10"]
            filterResult["PM2p5"] = currentData["PM2p5"]
            filterResult["CO"] = currentData["CO"]
            filterResult["CO2"] = currentData["CO2"]
            filterResult["NO2"] = currentData["NO2"]
            filterResult["SO2"] = currentData["SO2"]
            filterResult["O3"] = currentData["O3"]
            filterResult["noise"] = currentData["noise"]
            filterResult["rain"] = currentData["rain"]
            filterResult["TSP"] = currentData["TSP"]
            filterResult["receivedTime"] = currentData["receivedTime"]
            filterResult["rawAQI"] = (findAQIFromLiveData(currentData))

    return filterResult


def getAqmsConversion(data):
    if data.get("NO2") != None:
        data["NO2"] = (data["NO2"] * 0.0409 * 46.01) * 1000
    if data.get("S02") != None:
        data["SO2"] = (data["SO2"] * 0.0409 * 64.06) * 1000
    if data.get("O3") != None:
        data["NO2"] = (data["O3"] * 0.0409 * 48) * 1000
    if data.get("CO") != None:
        data["CO"] = (data["CO"] * 0.0409 * 28.01)
    if data.get("NH3") != None:
        data["NH3"] = (data["NH3"] * 0.0409 * 17.031) * 1000

    currentdate = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["receivedTime"] = int(time.time())
    return data


def updateStatusAQI(receivedTime, id):
    device = getDeviceFromId(id)

    if device != None:
        aqiUpdate = {"latestAQI": ""}
        if NEED_AQI == True:
            currentAQI = getStatParamHourly(device["logicalDeviceId"] + '_stat_daily', ["AQI"], None, None, 1, 0)

            if currentAQI != None:
                aqiUpdate = {"latestAQI": currentAQI}
        epoch_time = ''
        timeUpdate = {
            "lastDataReceiveTime": int(time.time()),
            "nearTimeStatus": ''
        }
        updates = {
            **aqiUpdate,
            **timeUpdate
        }

        updatedData = updateDocument('devices', {'deviceId': device["deviceId"]}, updates)


def updateDocument(documentName, query, data):
    collection = dbname['devices']
    updatedData = collection.update_one(query, {'$set': data})
    if updatedData != None:
        return True
    else:
        return False


def getStatParamHourly(collection_name, paramNameList, time_from, time_to, limit, offset):
    statQuery = {
        "paramName": {'$in': paramNameList},
        "key": {'$gte': time_from, '$lt': time_to}
    }
    if time_from == None and time_to == None:
        # statQuery = {
        #    "paramName":{'$in':paramNameList}
        # }
        statQuery = {
            "paramName": 'rawAQI'
        }
    result = GetFilteredDocumentSorted(collection_name, statQuery, {"_id": False, "epoch": False}, {"epoch": -1}, limit,
                                       offset)
    aqi = None
    if result == None:
        aqi = None
    else:
        aqi = result["statParams"]["sum"]
        aqi = str(round(aqi, 2))

    return aqi


def GetFilteredDocumentSorted(collectionName, query, excludFields, sortOptions, limitRecords, skipRecords):
    collection = dbname[collectionName]
    options = {}

    if sortOptions != None:
        options["sort"] = sortOptions
    else:
        options["sort"] = {"_id": -1}

    result = collection.find_one(query, excludFields)
    return result


def findAQIFromLiveData(currentData):
    resAqi = -1
    statForPm2p5 = None
    statForPm10 = None
    count = 0
    aqiValue = -9999999999

    paramValueMap = {}

    for paramName in currentData:
        if not isAQIApplicableForParamType(paramName):
            continue

        tempAvg = currentData[paramName]

        aqiVal = convertUgM3ToAqi(paramName.upper(), tempAvg)

        paramValueMap[paramName.upper()] = aqiVal

    for pname in paramValueMap:
        if pname == "PM2P5" or pname == "PM10" or pname == "SO2" or pname == "NO2" or pname == "NH3" or pname == "AsH3" or pname == "CO" or pname == "O3":

            if paramValueMap[pname] != None:
                count += 1

                aqiValue = max(aqiValue, paramValueMap[pname])

    if count >= 1:
        resAqi = aqiValue

    return resAqi


def isAQIApplicableForParamType(paramName):
    paramName = paramName.upper()
    if paramName == "PM2P5" or paramName == "PM10" or paramName == "SO2" or paramName == "NO2" or paramName == "CO" or paramName == "O3" or paramName == "NH3" or paramName == "C6H6":
        return True
    else:
        return False


# def updateDailyStats()

def convertUgM3ToAqi(paramName, value):
    result = 0
    temp = paramName.upper()

    paramFuncs = {
        "SO2": convertSO2u3ToAqi(value),
        "CO": convertCOu3ToAqi(value),
        "O3": convertO3u3ToAqi(value),
        "NH3": convertNH3u3ToAqi(value),
        "NO2": convertNoXu3ToAqi(value),
        "PM10": convertPM10u3ToAqi(value),
        "PM2P5": convertPM25u3ToAqi(value),
    }
    result = paramFuncs[temp]
    return result


def convertSO2u3ToAqi(value):
    if value <= 40:
        return value * 50 / 40
    elif value > 40 and value <= 80:
        return 50 + (value - 40) * 50 / 40
    elif value > 80 and value <= 380:
        return 100 + (value - 80) * 100 / 300
    elif value > 380 and value <= 800:
        return 200 + (value - 380) * (100 / 420)
    elif value > 800 and value <= 1600:
        return 300 + (value - 800) * (100 / 800)
    elif value > 1600 and value <= 2400:
        return 400 + (value - 1600) * (100 / 800)
    elif value > 2400:
        return (500)


def convertCOu3ToAqi(value):
    if value <= 1:
        return value * 50 / 1
    elif value > 1 and value <= 2:
        return 50 + (value - 1) * 50 / 1
    elif value > 2 and value <= 10:
        return 100 + (value - 2) * 100 / 8
    elif value > 10 and value <= 17:
        return 200 + (value - 10) * (100 / 7)
    elif value > 17 and value <= 34:
        return 300 + (value - 17) * (100 / 17)
    elif value > 34 and value <= 51:
        return 400 + (value - 34) * (100 / 17)
    elif (value > 51):
        return (500)


def convertO3u3ToAqi(value):
    if value <= 50:
        return value * 50 / 50
    elif value > 50 and value <= 100:
        return 50 + (value - 50) * 50 / 50
    elif value > 100 and value <= 168:
        return 100 + (value - 100) * 100 / 68
    elif value > 168 and value <= 208:
        return 200 + (value - 168) * (100 / 40)
    elif value > 208 and value <= 748:
        return 300 + (value - 208) * (100 / 539)
    elif value > 748 and value <= 939:
        return 400 + (value - 400) * (100 / 539)
    elif value > 939:
        return (500)


def convertNH3u3ToAqi(value):
    if value <= 200:
        return value * 50 / 200
    elif value > 200 and value <= 400:
        return 50 + (value - 200) * 50 / 200
    elif value > 400 and value <= 800:
        return 100 + (value - 400) * 100 / 400
    elif value > 800 and value <= 1200:
        return 200 + (value - 800) * (100 / 400)
    elif value > 1200 and value <= 1800:
        return 300 + (value - 1200) * (100 / 600)
    elif value > 1800 and value <= 2400:
        return 400 + (value - 1800) * (100 / 600)
    elif value > 2400:
        return (500)


def convertNoXu3ToAqi(value):
    if value <= 40:
        return value * 50 / 40
    elif value > 40 and value <= 80:
        return 50 + (value - 40) * 50 / 40
    elif value > 80 and value <= 180:
        return 100 + (value - 80) * 100 / 100
    elif value > 180 and value <= 280:
        return 200 + (value - 180) * 100 / 100
    elif value > 280 and value <= 400:
        return 300 + (value - 280) * (100 / 120)
    elif value > 400 and value <= 520:
        return 400 + (value - 400) * (100 / 120)
    elif value > 520:
        return (500)


def convertPM10u3ToAqi(value):
    if value <= 50:
        return value
    elif value > 50 and value <= 100:
        return value
    elif value > 100 and value <= 250:
        return 100 + (value - 100) * 100 / 150
    elif value > 250 and value <= 350:
        return 200 + (value - 250)
    elif value > 350 and value <= 430:
        return 300 + (value - 350) * (100 / 80)
    elif value > 430 and value <= 510:
        return 400 + (value - 430) * (100 / 80)
    elif value > 510:
        return (500)


def convertPM25u3ToAqi(value):
    if value <= 30:
        return value * 50 / 30
    elif value > 30 and value <= 60:
        return 50 + (value - 30) * 50 / 30
    elif value > 60 and value <= 90:
        return 100 + (value - 60) * 100 / 30
    elif value > 90 and value <= 120:
        return 200 + (value - 90) * 100 / 30
    elif value > 120 and value <= 250:
        return 300 + (value - 120) * 100 / 130
    elif value > 250 and value <= 380:
        return 400 + (value - 250) * 100 / 130
    elif value > 380:
        return (500)


def registerDevice(deviceDetails):
    device = createDeviceInstanceFromSubType(deviceDetails["subType"])
    # sub =
    isSubtypeExists = dbname["Sensor_Types"].find_one({"subType": deviceDetails["subType"]})
    response = deviceDetails
    response["paramDefinitions"] = device
    collectionName = "devices"
    collection = dbname[collectionName]
    isExists = collection.find_one({'deviceId': response["deviceId"]})
    if isExists or isSubtypeExists == None:
        return "failed"
    else:
        collection.insert_one(response)
        return "success"


def pushSensorData(deviceId, dataOfRequest):
    device = getDeviceFromId(deviceId)
    collectionName = "device_raw_data"
    collection = dbname[collectionName]
    if device != None:
        sampleData = dataOfRequest
        if device["location"] != None:
            location = device["location"]
            sampleData["latitude"] = location["latitude"]
            sampleData["longitude"] = location["longitude"]
            sampleData["location"] = location["city"]
            insetRowRaw = {
                "deviceId": deviceId,
                "logicalDeviceId": device["logicalDeviceId"],
                "status": "ready",
                "data": sampleData
            }

            collection.insert_one(insetRowRaw)
            return "success"
    else:
        return "failed"


def getDeviceFromId(devicId):
    collectionName = "devices"
    collection = dbname[collectionName]
    isDeviceExist = collection.find_one({'deviceId': devicId})
    if isDeviceExist:
        return isDeviceExist
    else:
        return None


def createDeviceInstanceFromSubType(subType):
    result = None
    newParamList = [
        {
            "filteringMethod": None,
            "filteringMethodDef": None,
            "paramName": "latitude",
        },
        {
            "filteringMethod": None,
            "filteringMethodDef": None,
            "paramName": "longitude",
        },
        {
            "filteringMethod": None,
            "filteringMethodDef": None,
            "paramName": "er_init_sensor",
            "displayName": 'Initialization Error',
            "paramType": 'error',
        },
        {
            "filteringMethod": None,
            "filteringMethodDef": None,
            "paramName": "er_read_sensor",
            "displayName": 'Read Error',
            "paramType": 'error',
        },
        {
            "filteringMethod": None,
            "filteringMethodDef": None,
            "paramName": "er_data_range",
            "displayName": 'Data Error',
            "paramType": 'error',
        },
        {
            "filteringMethod": None,
            "filteringMethodDef": None,
            "paramName": "er_system",
            "displayName": 'System Error',
            "paramType": 'error',
        }

    ]

    temp = newParamList

    specModule = sensorParameter()
    specModuleList = []

    sensorTypeCollection = dbname["Sensor_Types"]
    for x in sensorTypeCollection.find({"subType": subType}, {"deviceFamily": 1, "_id": 0}):
        deviceFamilyList = x["deviceFamily"]
        for families in deviceFamilyList:
            result = dbname["sensor_parameter"].find_one({"paramName": families})
            specModuleList.append(result)

    for x in range(len(newParamList)):
        specModuleList.append(newParamList[x])

    return specModuleList


def addDeviceParams(request):
    specModule = getParamDefinitions()
    collection = dbname['sensor_parameters']
    result = collection.insert_many(specModule)
    return HttpResponse("<h1>Hello and welcome to my first <u>Django App</u> project!</h1>")


def sensorParameter():
    collection = dbname['sensor_parameter']
    sensorParamList = []

    for x in collection.find({}, {'_id': False}):
        sensorParamList.append(x)
    return sensorParamList


def getParamDefinitions():
    paramDefinitons = [
        {
            "paramName": "temperature",
            "displayName": "Temperature",
            "displayNameHtml": "Temperature",
            "unit": "oC",
            "unitDisplayHtml": "<sup>o</sup>C",
            "isDisplayEnabled": True,
            "displayImage": "temperature.png",
            "isPrimary": False,
            "needsLiveData": True,
            "valuePrecision": 1,
            "isCsvParam": True,
            "isFilterable": True,
            "signageDisplayLive": True,
            "maxRanges": {
                "min": -10,
                "max": 80
            },
            "limits": [
                {
                    "max": 10,
                    "color": "00B050",
                    "description": "Cold"
                },
                {
                    "min": 10,
                    "max": 15,
                    "color": "92D050",
                    "description": "Cool"
                },
                {
                    "min": 15,
                    "max": 25,
                    "color": "FFFF00",
                    "description": "Warm"
                },
                {
                    "min": 25,
                    "max": 37,
                    "color": "FF9A00",
                    "description": "Hot"
                },
                {
                    "min": 37,
                    "max": 40,
                    "color": "FF0000",
                    "description": "Very Hot"
                },
                {
                    "min": 40,
                    "color": "800000",
                    "description": "Extremely Hot"
                }
            ]
        },
        {
            "paramName": "windspeed",
            "displayName": "Wind Speed",
            "displayNameHtml": "Wind Speed",
            "unit": "m/s",
            "unitDisplayHtml": "<sup>o</sup>C",
            "isDisplayEnabled": True,
            "displayImage": "temperature.png",
            "isPrimary": False,
            "needsLiveData": True,
            "valuePrecision": 1,
            "isCsvParam": True,
            "isFilterable": True,
            "signageDisplayLive": True,
            "maxRanges": {
                "min": 0,
                "max": 60
            },
            "limits": [

            ]
        },
        {
            "paramName": "winddirection",
            "displayName": "Wind Direction",
            "displayNameHtml": "Wind Direction",
            "unit": "degree",
            "unitDisplayHtml": "<sup>o</sup>C",
            "isDisplayEnabled": True,
            "displayImage": "temperature.png",
            "isPrimary": False,
            "needsLiveData": True,
            "valuePrecision": 1,
            "isCsvParam": True,
            "isFilterable": True,
            "signageDisplayLive": True,
            "maxRanges": {
                "min": 0,
                "max": 360
            },
            "limits": [

            ]
        },
        {
            "paramName": "pressure",
            "displayName": "Pressure",
            "displayNameHtml": "Pressure",
            "unit": "hPa",
            "unitDisplayHtml": "hPa",
            "displayImage": "pressure.png",
            "isDisplayEnabled": True,
            "needsLiveData": True,
            "isPrimary": False,
            "valuePrecision": 2,
            "isCsvParam": True,
            "isFilterable": True,
            "signageDisplayLive": True,
            "maxRanges": {
                "min": 540,
                "max": 1100
            },
            "limits": [
                {
                    "max": 980,
                    "color": "e4e9ed",
                    "description": "Low"
                },
                {
                    "min": 980,
                    "max": 1050,
                    "color": "00B050",
                    "description": "Normal"
                },
                {
                    "min": 1050,
                    "color": "800000",
                    "description": "High"
                }
            ]
        },
        {
            "paramName": "humidity",
            "displayName": "Humidity",
            "displayNameHtml": "Humidity",
            "unit": "%RH",
            "unitDisplayHtml": "%RH",
            "isDisplayEnabled": True,
            "needsLiveData": True,
            "isPrimary": False,
            "displayImage": "humidity.png",
            "valuePrecision": 2,
            "isCsvParam": True,
            "isFilterable": True,
            "signageDisplayLive": True,
            "maxRanges": {
                "min": 0,
                "max": 90
            },
            "limits": [
                {
                    "max": 25,
                    "color": "00B050",
                    "description": "Dry"
                },
                {
                    "min": 25,
                    "max": 60,
                    "color": "92D050",
                    "description": "Normal"
                },
                {
                    "min": 60,
                    "color": "FFFF00",
                    "description": "Moist"
                }
            ]
        },
        {
            "paramName": "PM10",
            "displayName": "PM10",
            "displayNameHtml": "PM<sub>10</sub>",
            "unit": "µg/m3",
            "unitDisplayHtml": "&mu;g/m<sup>3</sup>",
            "isDisplayEnabled": True,
            "needsLiveData": True,
            "isPrimary": False,
            "displayImage": "param.png",
            "valuePrecision": 2,
            "isCsvParam": True,
            "isFilterable": True,
            "signageDisplayStat": True,
            "maxRanges": {
                "min": 0,
                "max": 450
            },
            "limits": [
                {
                    "max": 50,
                    "color": "00B050",
                    "description": "Good"
                },
                {
                    "min": 50,
                    "max": 100,
                    "color": "92D050",
                    "description": "Satisfactory"
                },
                {
                    "min": 100,
                    "max": 250,
                    "color": "FFFF00",
                    "description": "Moderate"
                },
                {
                    "min": 250,
                    "max": 350,
                    "color": "FF9A00",
                    "description": "Poor"
                },
                {
                    "min": 350,
                    "max": 430,
                    "color": "FF0000",
                    "description": "Very Poor"
                },
                {
                    "min": 430,
                    "color": "800000",
                    "description": "Severe"
                }
            ]
        },
        {
            "paramName": "PM2p5",
            "displayName": "PM2.5",
            "displayNameHtml": "PM<sub>2.5</sub>",
            "unit": "µg/m3",
            "unitDisplayHtml": "&mu;g/m<sup>3</sup>",
            "isDisplayEnabled": True,
            "needsLiveData": True,
            "isPrimary": False,
            "displayImage": "param.png",
            "valuePrecision": 2,
            "isCsvParam": True,
            "isFilterable": True,
            "signageDisplayStat": True,
            "maxRanges": {
                "min": 0,
                "max": 230
            },
            "limits": [
                {
                    "max": 30,
                    "color": "00B050",
                    "description": "Good"
                },
                {
                    "min": 30,
                    "max": 60,
                    "color": "92D050",
                    "description": "Satisfactory"
                },
                {
                    "min": 60,
                    "max": 90,
                    "color": "FFFF00",
                    "description": "Moderate"
                },
                {
                    "min": 90,
                    "max": 120,
                    "color": "FF9A00",
                    "description": "Poor"
                },
                {
                    "min": 120,
                    "max": 250,
                    "color": "FF0000",
                    "description": "Very Poor"
                },
                {
                    "min": 250,
                    "color": "800000",
                    "description": "Severe"
                }
            ]
        },
        {
            "paramName": "TSP",
            "displayName": "PM100",
            "displayNameHtml": "PM<sub>100</sub>",
            "unit": "mg/m3",
            "unitDisplayHtml": "&mu;g/m<sup>3</sup>",
            "isDisplayEnabled": True,
            "needsLiveData": True,
            "isPrimary": False,
            "displayImage": "param.png",
            "valuePrecision": 2,
            "isCsvParam": True,
            "isFilterable": True,
            "signageDisplayStat": True,
            "maxRanges": {
                "min": 0,
                "max": 20
            },
            "limits": [
                {
                    "max": 30,
                    "color": "00B050",
                    "description": "Good"
                },
                {
                    "min": 30,
                    "max": 60,
                    "color": "92D050",
                    "description": "Satisfactory"
                },
                {
                    "min": 60,
                    "max": 90,
                    "color": "FFFF00",
                    "description": "Moderate"
                },
                {
                    "min": 90,
                    "max": 120,
                    "color": "FF9A00",
                    "description": "Poor"
                },
                {
                    "min": 120,
                    "max": 250,
                    "color": "FF0000",
                    "description": "Very Poor"
                },
                {
                    "min": 250,
                    "color": "800000",
                    "description": "Severe"
                }
            ]
        },
        {
            "paramName": "CO2",
            "displayName": "CO2",
            "displayNameHtml": "CO<sub>2</sub>",
            "unit": "PPM",
            "unitDisplayHtml": "PPM",
            "displayImage": "param.png",
            "needsLiveData": True,
            "isDisplayEnabled": True,
            "isPrimary": False,
            "isCsvParam": True,
            "isFilterable": True,
            "valuePrecision": 3,
            "signageDisplayStat": True,
            "maxRanges": {
                "min": 0,
                "max": 5000
            },
            "limits": [
                {
                    "max": 350,
                    "color": "00B050",
                    "description": "Good"
                },
                {
                    "min": 350,
                    "max": 1000,
                    "color": "92D050",
                    "description": "Satisfactory"
                },
                {
                    "min": 1000,
                    "max": 2000,
                    "color": "FFFF00",
                    "description": "Moderate"
                },
                {
                    "min": 2000,
                    "max": 5000,
                    "color": "FF9A00",
                    "description": "Poor"
                },
                {
                    "max": 5000,
                    "color": "FF0000",
                    "description": "Very Poor"
                }
            ]
        },
        {
            "paramName": "CO",
            "displayName": "CO",
            "displayNameHtml": "CO",
            "unit": "PPM",
            "unitDisplayHtml": "PPM",
            "displayImage": "param.png",
            "isFilteringEnabled": False,
            "needsLiveData": True,
            "isPrimary": False,
            "filteringMethod": None,
            "isDisplayEnabled": True,
            "valuePrecision": 3,
            "isCsvParam": True,
            "isFilterable": True,
            "signageDisplayStat": True,
            "maxRanges": {
                "min": 0,
                "max": 1000
            },
            "limits": [
                {
                    "max": 500,
                    "color": "00B050",
                    "description": "Good"
                },
                {
                    "min": 500,
                    "max": 1000,
                    "color": "92D050",
                    "description": "Satisfactory"
                },
                {
                    "min": 1000,
                    "max": 1500,
                    "color": "FFFF00",
                    "description": "Moderate"
                },
                {
                    "min": 1500,
                    "max": 2000,
                    "color": "FF9A00",
                    "description": "Poor"
                },
                {
                    "min": 2000,
                    "max": 2500,
                    "color": "FF0000",
                    "description": "Very Poor"
                },
                {
                    "min": 2500,
                    "color": "800000",
                    "description": "Severe"
                }
            ]
        },
        {
            "paramName": "NO2",
            "displayName": "NO2",
            "displayNameHtml": "NO<sub>2</sub>",
            "unit": "PPM",
            "unitDisplayHtml": "PPM",
            "needsLiveData": True,
            "displayImage": "param.png",
            "isDisplayEnabled": True,
            "isPrimary": False,
            "valuePrecision": 3,
            "isCsvParam": True,
            "isFilterable": True,
            "signageDisplayStat": True,
            "maxRanges": {
                "min": 0,
                "max": 2000
            },
            "limits": [
                {
                    "max": 500,
                    "color": "00B050",
                    "description": "Good"
                },
                {
                    "min": 500,
                    "max": 1000,
                    "color": "92D050",
                    "description": "Satisfactory"
                },
                {
                    "min": 1000,
                    "max": 1500,
                    "color": "FFFF00",
                    "description": "Moderate"
                },
                {
                    "min": 1500,
                    "max": 2000,
                    "color": "FF9A00",
                    "description": "Poor"
                },
                {
                    "min": 2000,
                    "max": 2500,
                    "color": "FF0000",
                    "description": "Very Poor"
                },
                {
                    "min": 2500,
                    "color": "800000",
                    "description": "Severe"
                }
            ]
        },
        {
            "paramName": "SO2",
            "displayName": "SO2",
            "displayNameHtml": "SO<sub>2</sub>",
            "unit": "PPM",
            "unitDisplayHtml": "PPM",
            "displayImage": "param.png",
            "needsLiveData": True,
            "isDisplayEnabled": True,
            "isPrimary": False,
            "valuePrecision": 3,
            "isCsvParam": True,
            "isFilterable": True,
            "signageDisplayStat": True,
            "maxRanges": {
                "min": 0,
                "max": 20
            },
            "limits": [
                {
                    "max": 500,
                    "color": "00B050",
                    "description": "Good"
                },
                {
                    "min": 500,
                    "max": 1000,
                    "color": "92D050",
                    "description": "Satisfactory"
                },
                {
                    "min": 1000,
                    "max": 1500,
                    "color": "FFFF00",
                    "description": "Moderate"
                },
                {
                    "min": 1500,
                    "max": 2000,
                    "color": "FF9A00",
                    "description": "Poor"
                },
                {
                    "min": 2000,
                    "max": 2500,
                    "color": "FF0000",
                    "description": "Very Poor"
                },
                {
                    "min": 2500,
                    "color": "800000",
                    "description": "Severe"
                }
            ]
        },
        {
            "paramName": "O3",
            "displayName": "O3",
            "displayNameHtml": "O<sub>3</sub>",
            "unit": "PPM",
            "unitDisplayHtml": "PPM",
            "needsLiveData": True,
            "displayImage": "param.png",
            "isDisplayEnabled": True,
            "isPrimary": False,
            "valuePrecision": 3,
            "isCsvParam": True,
            "signageDisplayStat": True,
            "isFilterable": True,
            "maxRanges": {
                "min": 0,
                "max": 1000
            },
            "limits": [
                {
                    "max": 46.5278,
                    "color": "00B050",
                    "description": "Good"
                },
                {
                    "min": 46.5278,
                    "max": 92.8593,
                    "color": "92D050",
                    "description": "Satisfactory"
                },
                {
                    "min": 92.8593,
                    "max": 156.0744,
                    "color": "FFFF00",
                    "description": "Moderate"
                },
                {
                    "min": 156.0744,
                    "max": 193.1788,
                    "color": "FF9A00",
                    "description": "Poor"
                },
                {
                    "min": 193.1788,
                    "max": 694.9728,
                    "color": "FF0000",
                    "description": "Very Poor"
                },
                {
                    "min": 694.9728,
                    "color": "800000",
                    "description": "Severe"
                }
            ]
        },
        {
            "paramName": "noise",
            "displayName": "Noise",
            "displayNameHtml": "Noise",
            "unit": "dBA",
            "unitDisplayHtml": "dBA",
            "isDisplayEnabled": True,
            "needsLiveData": True,
            "isPrimary": False,
            "displayImage": "megaphonegrey.png",
            "valuePrecision": 2,
            "isCsvParam": True,
            "signageDisplayLive": True,
            "maxRanges": {
                "min": 30,
                "max": 120
            },
            "limits": [
                {
                    "max": 40,
                    "color": "00B050",
                    "description": "Faint"
                },
                {
                    "min": 40,
                    "max": 80,
                    "color": "92D050",
                    "description": "Moderate"
                },
                {
                    "min": 80,
                    "max": 110,
                    "color": "FFFF00",
                    "description": "Loud"
                },
                {
                    "min": 110,
                    "max": 140,
                    "color": "FF9A00",
                    "description": "Pain"
                },
                {
                    "min": 140,
                    "color": "ff0000",
                    "description": "Intolerable"
                }
            ]
        },
        {
            "paramName": "rain",
            "displayName": "Rain",
            "displayNameHtml": "Rain",
            "unit": "mm",
            "unitDisplayHtml": "mm",
            "isDisplayEnabled": True,
            "needsLiveData": True,
            "isPrimary": False,
            "displayImage": "raingrey.png",
            "valuePrecision": 2,
            "needCumil": True,
            "needSpecific": True,
            "isCsvParam": True,
            "signageDisplayLive": True,
            "maxRanges": {
                "min": 0,
                "max": 999.8
            },
            "limits": [
                {
                    "max": 2.5,
                    "color": "92D050",
                    "description": "Light Rain"
                },
                {
                    "min": 2.5,
                    "max": 10,
                    "color": "FFFF00",
                    "description": "Moderate Rain"
                },
                {
                    "min": 10,
                    "max": 50,
                    "color": "FF9A00",
                    "description": "Heavy Rain"
                },
                {
                    "min": 50,
                    "color": "ff0000",
                    "description": "Violent"
                }
            ]
        },
        {
            "paramName": "UV",
            "displayName": "UV",
            "displayNameHtml": "UV",
            "unit": "nm",
            "unitDisplayHtml": "nm",
            "displayImage": "param.png",
            "needsLiveData": False,
            "isDisplayEnabled": False,
            "isPrimary": False,
            "valuePrecision": 2,
            "isCsvParam": True,
            "signageDisplayStat": True,
            "maxRanges": {
                "min": 0,
                "max": 65535
            },
            "limits": [
                {
                    "max": 280,
                    "color": "F68E3D",
                    "description": "Dangerous"
                },
                {
                    "min": 280,
                    "max": 315,
                    "color": "F0503D",
                    "description": "Burning"
                },
                {
                    "min": 315,
                    "color": "b51807",
                    "description": "Tanning"
                }
            ]
        },
        {
            "paramName": "lux",
            "displayName": "Light",
            "displayNameHtml": "Light",
            "unit": "lux",
            "unitDisplayHtml": "lux",
            "displayImage": "param.png",
            "needsLiveData": False,
            "isDisplayEnabled": False,
            "isPrimary": False,
            "valuePrecision": 2,
            "isCsvParam": True,
            "signageDisplayStat": True,
            "maxRanges": {
                "min": 0,
                "max": 35000
            },
            "limits": [
                {
                    "max": 1,
                    "color": "00ff85",
                    "description": "Equivalent to Twilight"
                },
                {
                    "min": 1,
                    "max": 2,
                    "color": "00ff2b",
                    "description": "Equivalent to risk lighting"
                },
                {
                    "min": 2,
                    "max": 5,
                    "color": "b0ff00",
                    "description": "Equivalent to side road lighting"
                },
                {
                    "min": 5,
                    "max": 10,
                    "color": "ccff00",
                    "description": "Equivalent to Sunset"
                },
                {
                    "min": 10,
                    "max": 15,
                    "color": "f0ff00",
                    "description": "Equivalent to main road lighting"
                },
                {
                    "min": 15,
                    "max": 50,
                    "color": "fff400",
                    "description": "Equivalent to passageway lighting"
                },
                {
                    "min": 50,
                    "max": 300,
                    "color": "ffce00",
                    "description": "Equivalent to easy reading lighting"
                },
                {
                    "min": 300,
                    "max": 500,
                    "color": "ffa700",
                    "description": "Equivalent to office lighting"
                },
                {
                    "min": 500,
                    "max": 5000,
                    "color": "ff6700",
                    "description": "Equivalent to overcast sky"
                },
                {
                    "min": 5000,
                    "color": "ff1a00",
                    "description": "Equivalent to summer"
                }
            ]
        },
        {
            "paramName": "receivedTime",
            "displayName": "receivedTime",
            "displayNameHtml": "receivedTime",
            "unit": "",
            "unitDisplayHtml": "",
            "displayImage": "param.png",
            "needsLiveData": False,
            "isDisplayEnabled": True,
            "isPrimary": False,
            "valuePrecision": 0,
            "maxRanges": None,
            "isCsvParam": False,
            "isFilterable": False,
            "signageDisplayLive": True,
            "valueType": "date"
        },
        {
            "paramName": "rawAQI",
            "displayName": "Raw AQI",
            "displayNameHtml": "Raw AQI",
            "unit": "",
            "unitDisplayHtml": "",
            "displayImage": "param.png",
            "needsLiveData": False,
            "isDisplayEnabled": True,
            "isPrimary": False,
            "valuePrecision": 0,
            "isDerivedParam": True,
            "isCsvParam": True,
            "isFilterable": False,
            "maxRanges": {
                "min": 0,
                "max": 500
            },
            "limits": [
                {
                    "max": 50,
                    "color": "00B050",
                    "description": "Good"
                },
                {
                    "min": 50,
                    "max": 100,
                    "color": "92D050",
                    "description": "Satisfactory"
                },
                {
                    "min": 100,
                    "max": 200,
                    "color": "FFFF00",
                    "description": "Moderate"
                },
                {
                    "min": 200,
                    "max": 300,
                    "color": "FF9A00",
                    "description": "Poor"
                },
                {
                    "min": 300,
                    "max": 400,
                    "color": "FF0000",
                    "description": "Very Poor"
                },
                {
                    "min": 400,
                    "color": "800000",
                    "description": "Severe"
                }
            ]
        },
        {
            "paramName": "AQI",
            "displayName": "AQI",
            "displayNameHtml": "AQI",
            "unit": "",
            "unitDisplayHtml": "",
            "displayImage": "param.png",
            "needsLiveData": True,
            "isDisplayEnabled": True,
            "isPrimary": True,
            "valuePrecision": 0,
            "isDerivedParam": True,
            "isCsvParam": True,
            "isFilterable": False,
            "signageDisplayAqiParam": True,
            "maxRanges": {
                "min": 0,
                "max": 500
            },
            "limits": [
                {
                    "max": 50,
                    "color": "00B050",
                    "description": "Good"
                },
                {
                    "min": 50,
                    "max": 100,
                    "color": "92D050",
                    "description": "Satisfactory"
                },
                {
                    "min": 100,
                    "max": 200,
                    "color": "FFFF00",
                    "description": "Moderate"
                },
                {
                    "min": 200,
                    "max": 300,
                    "color": "FF9A00",
                    "description": "Poor"
                },
                {
                    "min": 300,
                    "max": 400,
                    "color": "FF0000",
                    "description": "Very Poor"
                },
                {
                    "min": 400,
                    "color": "800000",
                    "description": "Severe"
                }
            ]
        },
        {
            "paramName": "prominentPollutant",
            "displayName": "Prominent Pollutant",
            "displayNameHtml": "Prominent Pollutant",
            "unit": "",
            "unitDisplayHtml": "",
            "displayImage": "param.png",
            "needsLiveData": False,
            "isDisplayEnabled": True,
            "isPrimary": False,
            "valuePrecision": 0,
            "maxRanges": None,
            "isCsvParam": True,
            "isFilterable": False,
            "signageDisplayAqiParam": True,
            "isDerived": True,
            "valueType": "string"
        }
    ]
    return paramDefinitons
