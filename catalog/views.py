from django.shortcuts import get_object_or_404, redirect, render

from .models import Item


def catalog_list(request):
    if not request.user.is_authenticated:
        return render(request, 'catalog/home.html')
    items = Item.objects.all()
    return render(request, 'catalog/catalog_list.html', {'items': items})


def catalog_details(request, item_id):
    if not request.user.is_authenticated:
        return redirect('catalog_list')
    item = get_object_or_404(Item, pk=item_id)
    return render(request, 'catalog/catalog_details.html', {'item': item})
