from django.core.paginator import Paginator
from django.shortcuts import render,redirect,get_object_or_404
from .models import Product,CartItem
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .forms import UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib import messages



def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')          
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('view_products')  # Redirect to product listing page
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')  # Redirect to login page

@never_cache
@login_required
def view_products(request):
    products = Product.objects.all()  
    paginator = Paginator(products, 3)  

    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number) 

    return render(request, 'view_products.html', {'page_obj': page_obj}) 

@never_cache
@login_required
def add_to_cart(request, product_id):
    """
    Adds a product to the user's cart. If the product is already in the cart,
    its quantity is increased by 1.
    """
    # Find the product by its ID or show a 404 error if it doesn't exist
    product = get_object_or_404(Product, id=product_id)
    
    # Check if the product is already in the user's cart
    cart_item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    
    if not created:
        # If the item already exists in the cart, increase the quantity
        cart_item.quantity += 1
        cart_item.save()
    
    # Redirect the user to the cart view
    return redirect('view_cart')  

@never_cache
@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        item.total_price = item.product.price * item.quantity  # Add a total_price attribute for each item

    total_price = sum(item.total_price for item in cart_items)  # Calculate the total price for the cart
    return render(request, 'cart.html', {'cart_items': cart_items, 'total_price': total_price})  

def remove_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
        
        if cart_item.quantity > 1:
            # Decrease the quantity by 1
            cart_item.quantity -= 1
            cart_item.save()
        else:
            # Remove the item if quantity is 1
            cart_item.delete()
    
    return redirect('view_cart')

@never_cache
@login_required
def checkout(request):
    # Get the user's cart items
    cart_items = CartItem.objects.filter(user=request.user)
    
    # Check if the cart is empty
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Please add items before proceeding to checkout.")
        return redirect('view_cart')  # Redirect back to the cart page

    # Calculate the total price of the cart
    for item in cart_items:
        item.total_price = item.product.price * item.quantity  # Add a total_price attribute for each item

    total_price = sum(item.total_price for item in cart_items)
    
    if request.method == 'POST':
        return redirect('order_confirmation')  # Redirect to an order confirmation page
    
    return render(request, 'checkout.html', {'cart_items': cart_items, 'total_price': total_price})

@never_cache
@login_required
def order_confirmation(request):
    return render(request, 'order_confirmation.html')
