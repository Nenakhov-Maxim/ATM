from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

def get_home_page(request):
  return render(request, 'analitycs.html')
