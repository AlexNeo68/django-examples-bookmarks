from django.contrib.auth import authenticate, login
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .forms import LoginForm, UserRegistrationForm, UserEditForm, ProfileEditForm
from .models import Contact, Profile
from django.views.decorators.http import require_POST

from django.contrib import messages


# Create your views here.
def user_login(request: HttpRequest):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, username=cd['username'], password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    if not Profile.objects.filter(user=user).exists():
                        Profile.objects.create(user=user)
                    return HttpResponse('Authenticated successfully')
                else:
                    return HttpResponse('Disable account')
            else:
                return HttpResponse('Invalid login')
    else:
        form = LoginForm()
    
    return render(request, 'account/login.html', {'form': form})

@login_required
def dashboard(request: HttpRequest):
    return render(request, 'account/dashboard.html', {'section': 'dashboard'})


def register(request: HttpRequest):
    
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            Profile.objects.create(user=new_user)
            return render(request, 'account/register_done.html', {'new_user': new_user})

    else:
        user_form = UserRegistrationForm()

    return render(request, 'account/register.html', {'user_form': user_form})


@login_required
def edit(request:HttpRequest):
    if request.method == "POST":
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile, data=request.POST, files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
        else:
            messages.error(request, 'Error updating your profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)


    data = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'account/edit.html', data)

@login_required
def user_list(request: HttpRequest):
    users = User.objects.filter(is_active=True)
    context = {
        'section': 'peoples',
        'users': users
    }
    return render(request, 'account/user/list.html', context)

@login_required
def user_detail(request: HttpRequest, username):
    user = get_object_or_404(User, username=username, is_active=True)
    context = {
        'section': 'peoples',
        'user': user
    }
    return render(request, 'account/user/detail.html', context)

@require_POST
@login_required
def user_follow(request):
    user_id = request.POST.get('id')
    action = request.POST.get('action')
    if user_id and action:
        try:
            user = User.objects.get(id=user_id)
            if action == 'follow':
                Contact.objects.get_or_create(user_from=request.user, user_to=user)
                # create_action(request.user, 'is following', user)
            else:
                Contact.objects.filter(user_from=request.user, user_to=user).delete()
            return JsonResponse({'status': 'ok'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error'})
    return JsonResponse({'status': 'error'})
