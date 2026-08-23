from django.shortcuts import get_object_or_404, render

from .models import Item


def catalog_list(request):
    items = Item.objects.all()
    return render(request, 'catalog/catalog_list.html', {'items': items})

def catalog_details(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    return render(request, 'catalog/catalog_details.html', {'item': item})
