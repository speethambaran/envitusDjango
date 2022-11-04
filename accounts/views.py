import pymongo
from django.contrib import auth, messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from accounts.models import User
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
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        collection = dbname["accounts_user"]

        if collection.find_one({"username": request.POST["username"]}):
            # errorResponse["message"] = 'user already exists'
            # return JsonResponse(errorResponse, safe=False)
            messages.info(request, "Username already taken")
            return render(request, 'registration/register.html')

        elif collection.find_one({"email": request.POST["email"]}):
            # errorResponse["message"] = 'email already exists'
            # return JsonResponse(errorResponse, safe=False)
            messages.info(request, "Email already taken")
            return render(request, 'registration/register.html')
        elif pass1 != pass2:
            # errorResponse["message"] = 'password not match!'
            # return JsonResponse(errorResponse, safe=False)
            messages.info(request, "Password not match")
            return render(request, 'registration/register.html')
        else:
            myuser = User.objects.create_user(username=username, email=email, password=pass1)
            myuser.save()
            # hubResponse["message"] = 'user created successfully '
            # return JsonResponse(hubResponse, safe=False)
            messages.info(request, "User Created SuccessFully")
            return render(request, 'registration/login.html')
    # return JsonResponse(errorResponse, safe=False)
    return render(request, 'registration/register.html')


@csrf_exempt
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        collection = dbname["accounts_user"]

        if user is not None:
            return redirect('index')

        else:
            messages.error(request, "invalid user name password !")
            return redirect('registration/login')
    return render(request, 'registration/login.html')

@csrf_exempt
def users(request):
    userList = User.objects.all()
    return render(request, 'users.html', {'users': userList})

def getusers(request):
    data = []
    collection = dbname["accounts_user"]
    if request.method == 'GET':
        for x in dbname["accounts_user"].find({}, {'_id': 0}):
            data.append(x)
        hubResponse["data"] = data
    return JsonResponse(hubResponse)

@csrf_exempt
def enableusers(request):
    if request.method == 'POST':
        myuser = json.loads(request.body)
        collection = dbname["accounts_user"]
        isUserExists = collection.find_one({'username': myuser['username']})
        print(isUserExists)
        if isUserExists:
            collection.update_one({'username': myuser['username']}, {'$set': {'is_active': myuser['is_active']}})
            hubResponse["message"] = 'user status has been enabled '
            return JsonResponse(hubResponse, safe=False)
        else:
            errorResponse['message'] = 'error please try again '
            return JsonResponse(errorResponse, safe=False)
    return JsonResponse(errorResponse)

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
        if  isUserExists:
            collection.update_one({'username': request.POST['username']}, {'$set': {'role': request.POST['role']}})
            messages.info(request, "User role has been updated")
            return render(request, 'users.html')
        else:
            messages.info(request, "Error Please try again ")
            return render(request, 'roles.html')
    return render(request, 'roles.html')

