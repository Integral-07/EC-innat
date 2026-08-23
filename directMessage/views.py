from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def inbox(request):
    return render(request, 'directMessage/inbox.html')
