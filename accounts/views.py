import pymongo
from django.contrib import auth, messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from accounts.models import User, Organization
import json
from django.http import JsonResponse

# Create your views here.
client = pymongo.MongoClient('mongodb://localhost:27017')
dbname = client['accounts']

hubResponse = {"status": "ok", "errorCode": 0, "message": "None"}
errorResponse = {"status": 'error', "errorCode": -1, "message": "failed"}


@csrf_exempt
def index(request):
    return render(request, 'index.html')


@csrf_exempt
def register(request):
    if request.method == 'POST':
        myuser = json.loads(request.body)
        username = myuser['username']
        email = myuser['email']
        name = myuser['name']
        phone = myuser['phone']
        password = myuser['password']

        collection = dbname["accounts_user"]

        if collection.find_one({"username": myuser["username"]}):
            errorResponse["message"] = 'user already exists'
            return JsonResponse(errorResponse, safe=False)
            # messages.info(request, "Username already taken")
            # return render(request, 'register.html')

        elif collection.find_one({"email": myuser["email"]}):
            errorResponse["message"] = 'email already exists'
            return JsonResponse(errorResponse, safe=False)
            # messages.info(request, "Email already taken")
            # return render(request, 'register.html')
        elif password != password:
            errorResponse["message"] = 'password not match!'
            return JsonResponse(errorResponse, safe=False)
            # messages.info(request, "Please enter a valid Password")
            # return render('register')
        else:
            myuser = User.objects.create_user(username=username, email=email, name=name, phone=phone, password=password)
            myuser.save()
            hubResponse["message"] = 'user created successfully '
            return JsonResponse(hubResponse, safe=False)
            # messages.info(request, "User Created SuccessFully")
            # return render(request, 'login.html')
    return JsonResponse(errorResponse, safe=False)
    # return render(request, 'register.html')


@csrf_exempt
def login(request):
    if request.method == 'POST':
        userdata = json.loads(request.body)
        username = userdata['username']
        password = userdata['password']
        user = authenticate(request, username=username, password=password)

        collection = dbname["accounts_user"]

        if user is not None:
            data = {}
            Response ={}
            data['username'] = user.get_username()
            data['role'] = user.role
            Response["message"] = 'user logged in  successfully'
            Response['data'] = data
            return JsonResponse(Response, safe=False)
        else:
            errorResponse["message"] = 'invalid username or password'
            return JsonResponse(errorResponse, safe=False)
    return JsonResponse(errorResponse)


@csrf_exempt
def logout(request):
    if request.method == 'POST':
        logout(request)
        hubResponse["message"] = "User Logged Out Successfully"
        return JsonResponse(hubResponse, safe=False)
    else:
        errorResponse["message"] = "Error in  logout"
        return JsonResponse(errorResponse, safe=False)

@csrf_exempt
def users(request):
    userList = User.objects.all()
    role = User.Role.choices
    rolearr = []
    for x in role:
        rolearr.append(x[1])
    return render(request, 'users.html', {'users': userList, 'roles': rolearr})


def getusers(request):
    data = []
    collection = dbname["accounts_user"]
    if request.method == 'GET':
        for x in dbname["accounts_user"].find({}, {'_id': 0}):
            data.append(x)
        hubResponse["message"] = data
    return JsonResponse(hubResponse)


def userprofile(request, username):
    user = User.objects.get(username=username)
    return render(request, 'userprofile.html', {'users': user})


def editprofile(request, username):
    user = User.objects.get(username=username)
    role = User.Role.choices
    rolearr = []
    for x in role:
        rolearr.append(x[1])
    return render(request, 'editprofile.html', {'users': user, 'roles': rolearr})


@csrf_exempt
def enableusers(request):
    if request.method == 'POST':
        myuser = json.loads(request.body)
        collection = dbname["accounts_user"]
        isUserExists = collection.find_one({'username': myuser['username']})
        print(isUserExists)
        if isUserExists:
            collection.update_one({'username': myuser['username']},
                                  {'$set': {'is_active': myuser['is_active']}})
            hubResponse["message"] = 'user status has been enabled '
            return JsonResponse(hubResponse, safe=False)
            # return render(request, 'users.html')
        else:
            # return render(request, 'editprofile.html')
            errorResponse['message'] = 'error please try again '
            return JsonResponse(errorResponse, safe=False)
    return JsonResponse(errorResponse)


@csrf_exempt
def disableusers(request):
    if request.method == 'POST':
        myuser = json.loads(request.body)
        collection = dbname["accounts_user"]
        isUserExists = collection.find_one({'username': myuser['username']})
        if isUserExists:
            collection.update_one({'username': myuser['username']}, {'$set': {'is_active': myuser['is_active']}})
            hubResponse["message"] = 'user status has been disabled '
            return JsonResponse(hubResponse, safe=False)
        else:
            errorResponse['message'] = 'error please try again '
            return JsonResponse(errorResponse, safe=False)
    return JsonResponse(errorResponse)


@csrf_exempt
def roles(request):
    if request.method == 'POST':
        userdata = json.loads(request.body)
        collection = dbname["accounts_user"]
        isUserExists = collection.find_one({'username': userdata['username']})
        if isUserExists:
            collection.update_one({'username': userdata['username']}, {'$set': {'role': userdata['role']}})
            # messages.info(request, "User role has been updated")
            # return render(request, 'users.html')
            hubResponse["message"] = 'User role has been updated '
            return JsonResponse(hubResponse, safe=False)
        else:
            # messages.info(request, "Error Please try again ")
            # return render(request, 'editprofile.html')
            # return render(request, 'editprofile.html')
            errorResponse['message'] = 'No User Exist '
            return JsonResponse(errorResponse, safe=False)
    return JsonResponse(errorResponse)


@csrf_exempt
def deleteuser(request):
    if request.method == 'POST':
        user_data = json.loads(request.body)

        collection = dbname["accounts_user"]
        isUserExists = collection.find_one({'id': user_data['id']})
        collection.delete_one(isUserExists)
        hubResponse["message"] = 'User has been deleted '
        return JsonResponse(hubResponse, safe=False)
        # return redirect('users')
    else:
        return JsonResponse(errorResponse)
        # return render(request, 'userprofile.html')


@csrf_exempt
def addorganization(request):
    if request.method == 'POST':
        user_data = json.loads(request.body)
        collection = dbname["accounts_organization"]
        name = user_data['name']
        description = user_data['description']
        default = user_data['default']
        users = user_data['users']
        devices = user_data['devices']
        isExists = collection.find_one({'name': user_data['name']})
        if isExists:
            errorResponse["message"] = "Ogranization already exists"
            return JsonResponse(errorResponse)
        else:
            myuser = Organization(name=name, description=description, default=default, users=users, devices=devices)
            myuser.save()
            hubResponse["message"] = "Organization has been added"
            return JsonResponse(hubResponse, safe=False)
    return JsonResponse(errorResponse)


@csrf_exempt
def getorganization(request):
    data = []
    if request.method == 'GET':
        collection = dbname["accounts_organization"]
        for x in dbname["accounts_organization"].find({}, {'_id': 0}):
            data.append(x)
        hubResponse["message"] = data
        return JsonResponse(hubResponse, safe=False)
    return JsonResponse(errorResponse)


@csrf_exempt
def updateorganization(request):
    if request.method == 'POST':
        userdata = json.loads(request.body)
        collection = dbname["accounts_organization"]
        isOrgExists = collection.find_one({'id': userdata['id']})
        if isOrgExists:
            collection.update_one({'id': userdata['id']}, {'$set': {'name': userdata['name']}}, )
            collection.update_one({'id': userdata['id']}, {'$set': {'description': userdata['description']}}, )
            collection.update_one({'id': userdata['id']}, {'$set': {'default': userdata['default']}}, )
            collection.update_one({'id': userdata['id']}, {'$set': {'users': userdata['users']}}, )
            collection.update_one({'id': userdata['id']}, {'$set': {'devices': userdata['devices']}}, )
            hubResponse["message"] = 'Organization has been updated '
            return JsonResponse(hubResponse, safe=False)
        else:
            errorResponse['message'] = 'No Organization Exist '
            return JsonResponse(errorResponse, safe=False)
    return JsonResponse(errorResponse)


@csrf_exempt
def deleteorganization(request):
    if request.method == 'POST':
        user_data = json.loads(request.body)
        collection = dbname["accounts_organization"]
        isOrgExists = collection.find_one({'id': user_data['id']})
        if isOrgExists:
            collection.delete_one(isOrgExists)
            hubResponse["message"] = 'Organization has been deleted '
            return JsonResponse(hubResponse, safe=False)
        else:
            errorResponse["message"] = 'No Organization Exist '
            return JsonResponse(errorResponse, safe=False)
    return JsonResponse(errorResponse ,safe=False)
