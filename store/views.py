from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from .models import Product, Category, Order, OrderProduct, Customer
from .forms import *
from django.contrib import messages
from .utils import *
from django.db.models import Q
from shop import settings
from datetime import datetime
from django.core.mail import send_mail


class ProductList(ListView):
    model = Product
    context_object_name = 'categories'
    template_name = 'store/product_list.html'

    def get_queryset(self):
        categories = Category.objects.all()
        data = []
        for category in categories:
            products = Product.objects.filter(category=category)[:4]
            data.append({
                'title': category.title,
                'products': products
            })
        return data

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ProductList, self).get_context_data()
        context['title'] = 'Главная'
        return context


class ProductListByCategory(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'store/category_product_list.html'

    def get_queryset(self):
        sort_field = self.request.GET.get('sort')
        products = Product.objects.filter(category_id=self.kwargs['pk'])
        if sort_field:
            products = products.order_by(sort_field)

        return products


class SearchedProducts(ProductListByCategory):

    def get_queryset(self):
        searched_word = self.request.GET.get('q')
        products = Product.objects.filter(
            Q(name__icontains=searched_word) |
            Q(description__icontains=searched_word)
        )
        return products


class ProductDetail(DetailView):
    model = Product
    context_object_name = 'product'


def cart(request):
    cart = get_cart_data(request)
    context = {
        'cart_products_quantity': cart['cart_products_quantity'],
        'order': cart['order'],
        'items': cart['products']
    }

    return render(request, 'store/cart.html', context)


def checkout(request):
    cart = get_cart_data(request)
    context = {
        'cart_products_quantity': cart['cart_products_quantity'],
        'order': cart['order'],
        'items': cart['products'],
        'customer_form': CustomerForm(),
        'shipping_form': ShippingForm()
    }

    return render(request, 'store/checkout.html', context)


def to_cart(request, product_id, action):
    if not request.user.is_authenticated:
        session_cart = CartForAnonymousUser(request, product_id=product_id, action=action)
    else:
        cart = CartForAuthenticatedUser(request, product_id=product_id, action=action)

    next_page = request.META.get('HTTP_REFERER', 'product_list')
    return redirect(next_page)


def process_order(request):
    transaction_id = datetime.now().timestamp()
    data = request.POST

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        cart = CartForAuthenticatedUser(request)
    else:
        customer, order = anonymous_order(request, data)
        cart = CartForAnonymousUser(request)

    total = order.cart_total_price
    order.transaction_id = transaction_id

    order.complete = True
    order.save()

    shipping_info = ShippingAddress.objects.create(
        customer=customer,
        order=order,
        address=data['address'],
        city=data['city'],
        state=data['state'],
        zipcode=data['zipcode'],
    )

    product_list = ''

    for item in order.orderproduct_set.all():
        product_list += f'{item.product.name}: {item.quantity} шт. Цена: ${item.total_price}\n\n'

    message_to_user = f'''Здравствуйте, {customer.name}!

Ваш заказ принят на обработку.

Заказанные товары: 

{product_list}

Общее количество товаров: {order.cart_products_quantity}
Общая стоимость товаров: ${order.cart_total_price}

Для подтверждения заказа с вами свяжутся в ближайшее время.
'''

    message_to_owner = f'''
Заказ #{order.transaction_id}

Заказанные товары: 
{product_list}

Общее количество товаров: {order.cart_products_quantity}
Общая стоимость товаров: ${order.cart_total_price}

Информация о покупателе: 

Имя: {customer.name}
Email: {customer.email}
Телефон: {data['phone']}
Адрес: {data['address']}
Город: {data['city']}
Регион: {data['state']}
Индекс: {data['zipcode']} 
'''
    # print(message_to_user)
    print(customer)

    send_mail(
        'Оформление заказа',
        message_to_user,
        settings.EMAIL_HOST_USER,
        [customer.email],
    )

    send_mail(
        'Обработка заказа',
        message_to_owner,
        settings.EMAIL_HOST_USER,
        [settings.EMAIL_HOST_USER],
    )
    messages.success(request, 'Заказ оформлен и отправлен на обработку')
    cart.clear()
    return redirect('product_list')


# ---------------------------USERS START---------------------------
def user_form(request):
    login_form = LoginForm()
    registration_form = RegistrationForm()

    context = {
        'login_form': login_form,
        'registration_form': registration_form
    }

    return render(request, 'store/user_form.html', context)


def user_login(request):
    form = LoginForm(data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('product_list')
    else:
        messages.error(request, 'Неверное имя пользователя или пароль')
        return redirect('user_form')


def register(request):
    form = RegistrationForm(data=request.POST)
    if form.is_valid():
        user = form.save()
        messages.success(request, 'Отлично! Вы успешно зарегистрировались!')
    else:
        messages.error(request, form.errors)
    return redirect('user_form')


def user_logout(request):
    logout(request)
    return redirect('product_list')


def profile(request):
    return render(request, 'store/profile.html')


# ---------------------------USERS END ---------------------------

'''
Сделать так, чтобы спан у корзины отображался везде
'''