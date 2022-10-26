from django.shortcuts import render, redirect
from .forms import SignUpForm, LoginForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.template import loader
from .models import User, AbstractUser, Super_Admin, Administrator, Operator, Supervisor


def index(request):
    return render(request, 'index.html')


def register(request):
    msg = None
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            msg = 'user created'
            return redirect('login_view')
        else:
            msg = 'form is not valid'
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form, 'msg': msg})


def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.Super_Admin:
                login(request, user)
                return redirect('admin')
            elif user is not None and user.Administrator:
                login(request, user)
                return redirect('administrator')
            elif user is not None and user.Supervisor:
                login(request, user)
                return redirect('supervisor')
            elif user is not None and user.Operator:
                login(request, user)
                return redirect('operator')
            else:
                msg = 'invalid credentials'
        else:
            msg = 'error validating form'
    return render(request, 'login.html', {'form': form, 'msg': msg})


def admin(request):
    admindata = Super_Admin.objects.all().values()
    template = loader.get_template('admin.html')
    context = {
        'username': admindata,
    }
    return HttpResponse(template.render(context, request))


def administrator(request):
    administratordata = Administrator.objects.all().values()
    template = loader.get_template('administrator.html')
    context = {
        'username': administratordata,
    }
    return HttpResponse(template.render(context, request))


def supervisor(request):
    supervisordata = Supervisor.objects.all().values()
    template = loader.get_template('supervisor.html')
    context = {
        'username': supervisordata,
    }
    return HttpResponse(template.render(context, request))


def operator(request):
    operatordata = Operator.objects.all().values()
    template = loader.get_template('operator.html')
    context = {
        'username': operatordata,
    }
    return HttpResponse(template.render(context, request))
