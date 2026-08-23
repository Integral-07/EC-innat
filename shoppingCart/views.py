from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Item
from payments.services import EmptyCartError, checkout

from .models import CartItem


@login_required
def cart_detail(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('item')
    total = sum(ci.subtotal for ci in cart_items)
    return render(request, 'shoppingCart/cart_detail.html', {'cart_items': cart_items, 'total': total})


@login_required
@require_POST
def cart_item_create(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if not item.is_soldout:
        cart_item, created = CartItem.objects.get_or_create(user=request.user, item=item)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    return redirect('cart_detail')


@login_required
@require_POST
def cart_item_delete(request, item_id):
    CartItem.objects.filter(user=request.user, item_id=item_id).delete()
    return redirect('cart_detail')


@login_required
@require_POST
def cart_checkout(request):
    cart_items = CartItem.objects.filter(user=request.user).select_related('item')
    try:
        order = checkout(request.user, cart_items)
    except EmptyCartError:
        messages.error(request, 'カートが空です。')
        return redirect('cart_detail')
    return redirect('order_detail', order_id=order.id)
