from django.shortcuts import render


def home(request):
    return render(request, 'index.html')

def blogs(request):
    return render(request, 'blogs.html')