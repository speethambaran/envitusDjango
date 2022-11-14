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
        # myuser = json.loads(request.body)
        username = request.POST['username']
        email = request.POST['email']
        name = request.POST['name']
        password = request.POST['password']

        collection = dbname["accounts_user"]

        if collection.find_one({"username": request.POST["username"]}):
            # errorResponse["message"] = 'user already exists'
            # return JsonResponse(errorResponse, safe=False)
            messages.info(request, "Username already taken")
            return render(request, 'accounts.html')

        elif collection.find_one({"email": request.POST["email"]}):
            # errorResponse["message"] = 'email already exists'
            # return JsonResponse(errorResponse, safe=False)
            messages.info(request, "Email already taken")
            return render(request, 'accounts.html')
        elif password != password:
            # errorResponse["message"] = 'password not match!'
            # return JsonResponse(errorResponse, safe=False)
            messages.info(request, "Please enter a valid Password")
            return render('accounts')
        else:
            myuser = User.objects.create_user(username=username, email=email, name=name, password=password)
            myuser.save()
            # hubResponse["message"] = 'user created successfully '
            # return JsonResponse(hubResponse, safe=False)
            messages.info(request, "User Created SuccessFully")
            return render(request, 'login.html')
    # return JsonResponse(errorResponse, safe=False)
    return render(request, 'accounts.html')


@csrf_exempt
def login(request):
    if request.method == 'POST':
        # myuser = json.loads(request.body)
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        collection = dbname["accounts_user"]

        if user is not None:
            # hubResponse["message"] = 'user logged successfully'
            # return JsonResponse(hubResponse, safe=False)
            return redirect('index')

        else:
            # errorResponse["message"] = 'error login'
            # return JsonResponse(errorResponse, safe=False)
            messages.error(request, "invalid user or name password !")
            return redirect('login')
    return render(request, 'login.html')


def logout(request):
    logout(request)
    return render(request, 'login.html')


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
        hubResponse["data"] = data
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
        # myuser = json.loads(request.body)
        collection = dbname["accounts_user"]
        isUserExists = collection.find_one({'username': request.POST['username']})
        print(isUserExists)
        if isUserExists:
            collection.update_one({'username': request.POST['username']},
                                  {'$set': {'is_active': request.POST['is_active']}})
            # hubResponse["message"] = 'user status has been enabled '
            # return JsonResponse(hubResponse, safe=False)
            return render(request, 'users.html')
        else:
            return render(request, 'editprofile.html')
    #         errorResponse['message'] = 'error please try again '
    #         return JsonResponse(errorResponse, safe=False)
    # return JsonResponse(errorResponse)


@csrf_exempt
def disableusers(request):
    if request.method == 'POST':
        myuser = json.loads(request.body)
        collection = dbname["accounts_user"]
        isUserExists = collection.find_one({'username': myuser['username']})
        print(isUserExists)
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
        collection = dbname["accounts_user"]

        isUserExists = collection.find_one({'username': request.POST['username']})
        if isUserExists:
            collection.update_one({'username': request.POST['username']}, {'$set': {'role': request.method['role']}})
            messages.info(request, "User role has been updated")
            return render(request, 'users.html')
            # hubResponse["message"] = 'User role has been updated '
            # return JsonResponse(hubResponse, safe=False)
        else:
            messages.info(request, "Error Please try again ")
            return render(request, 'editprofile.html')
    return render(request, 'editprofile.html')
    #     errorResponse['message'] = 'error please try again '
    #     return JsonResponse(errorResponse, safe=False)
    # return JsonResponse(errorResponse)


@csrf_exempt
def deleteuser(request, id):
    user = User.objects.get(id=id)
    user.delete()
    return redirect('users')
    # if request.method == 'POST':
    #     # user_data = json.loads(request.body)
    #
    #     collection = dbname["accounts_user"]
    #     isUserExists = collection.find_one({'id': request.POST['id']})
    #     collection.delete_one(isUserExists)
    #     # hubResponse["message"] = 'User has been deleted '
    #     # return JsonResponse(hubResponse, safe=False)
    #     return redirect('users')
    # else:
    #     return render(request, 'userprofile.html')


@csrf_exempt
def addorganization(request):
    if request.method == 'POST':
        myuser = json.loads(request.body)
        name = myuser['name']
        description = myuser['description']
        default = myuser['default']
        users = myuser['users']
        devices = myuser['devices']
        collection = dbname["organization"]
        isOrganizationExists = collection.find_one({name: myuser['name']})
        if isOrganizationExists:
            errorResponse["message"] = 'name already exists'
            return JsonResponse(errorResponse, safe=False)
        else:
            myuser = Organization(name=name, description=description, default=default, users=users, devices=devices)
            myuser.save()
            hubResponse["message"] = "Organization has been added"
            return JsonResponse(hubResponse, safe=False)
    return JsonResponse(errorResponse)
