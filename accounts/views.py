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
        password = request.POST['password']

        collection = dbname["accounts_user"]

        if collection.find_one({"username": request.POST["username"]}):
            # errorResponse["message"] = 'user already exists'
            # return JsonResponse(errorResponse, safe=False)
            messages.info(request, "Username already taken")
            return render(request, 'register.html')

        elif collection.find_one({"email": request.POST["email"]}):
            # errorResponse["message"] = 'email already exists'
            # return JsonResponse(errorResponse, safe=False)
            messages.info(request, "Email already taken")
            return render(request, 'register.html')
        elif password != password:
            # errorResponse["message"] = 'password not match!'
            # return JsonResponse(errorResponse, safe=False)
            messages.info(request, "Please enter a valid Password")
            return render('register')
        else:
            myuser = User.objects.create_user(username=username, email=email, password=password)
            myuser.save()
            # hubResponse["message"] = 'user created successfully '
            # return JsonResponse(hubResponse, safe=False)
            messages.info(request, "User Created SuccessFully")
            return render(request, 'login.html')
    # return JsonResponse(errorResponse, safe=False)
    return render(request, 'register.html')


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
            messages.error(request, "invalid user or name password !")
            return redirect('login')
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
        print('user data : ', json.loads(request.body))

        user_data = json.loads(request.body)

        collection = dbname["accounts_user"]

        isUserExists = collection.find_one({'username': user_data['username']})
        if isUserExists:
            collection.update_one({'username': user_data['username']}, {'$set': {'role': user_data['role']}})
            # messages.info(request, "User role has been updated")
            # return render(request, 'users.html')
            hubResponse["message"] = 'User role has been updated '
            return JsonResponse(hubResponse, safe=False)
        else:
            # messages.info(request, "Error Please try again ")
            # return render(request, 'users.html')
            # return render(request, 'users.html')
            errorResponse['message'] = 'error please try again '
            return JsonResponse(errorResponse, safe=False)
        return JsonResponse(errorResponse)


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
