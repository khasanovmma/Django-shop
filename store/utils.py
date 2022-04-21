from .models import *
from shop import settings


class CartForAnonymousUser:

    def __init__(self, request, product_id=None, action=None):
        self.session = request.session
        self.cart = self.get_cart()

        if action == 'add':
            self.add(product_id)
        elif action == 'delete':
            self.delete(product_id)

    def get_cart(self):
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session['cart'] = {}
        return cart

    def add(self, product_id):
        key = str(product_id)
        product = Product.objects.get(pk=product_id)
        cart_product = self.cart.get(key)

        if product.quantity > 0:
            if cart_product:
                cart_product['quantity'] += 1
            else:
                self.cart[key] = {
                    'quantity': 1
                }
            product.quantity -= 1
            product.save()
        self.save()

    def delete(self, product_id):
        key = str(product_id)
        product = Product.objects.get(pk=product_id)
        cart_product = self.cart.get(key)

        cart_product['quantity'] -= 1
        product.quantity += 1

        if cart_product['quantity'] <= 0:
            del self.cart[key]

        product.save()
        self.save()

    def get_cart_info(self):
        items = []
        order = {
            'cart_total_price': 0,
            'cart_products_quantity': 0,
            'shipping': True
        }
        cart_products_quantity = order['cart_products_quantity']

        for key in self.cart:
            if self.cart[key]['quantity'] > 0:
                cart_products_quantity += self.cart[key]['quantity']

                product = Product.objects.get(pk=key)
                total_price = product.price * self.cart[key]['quantity']

                order['cart_total_price'] += total_price
                order['cart_products_quantity'] += self.cart[key]['quantity']

                item = {
                    'pk': product.pk,
                    'product': {
                        'pk': product.pk,
                        'name': product.name,
                        'price': product.price,
                        'image_url': product.image_url,
                    },
                    'quantity': self.cart[key]['quantity'],
                    'total_price': total_price,
                }
                items.append(item)
        self.save()
        return {
            'order': order,
            'products': items,
            'cart_products_quantity': cart_products_quantity
        }

    def save(self):
        self.session.modified = True

    def clear(self):
        self.cart.clear()


class CartForAuthenticatedUser:

    def __init__(self, request, product_id=None, action=None):
        self.user = request.user

        if action == 'add':
            self.add(product_id)
        elif action == 'delete':
            self.delete(product_id)

    def get_cart_info(self):
        customer, created = Customer.objects.get_or_create(
            user=self.user,
            name=self.user.username,
            email=self.user.email)

        order, created = Order.objects.get_or_create(customer=customer, complete=False)
        products = order.orderproduct_set.all()
        cart_products_quantity = order.cart_products_quantity

        return {
            'order': order,
            'products': products,
            'cart_products_quantity': cart_products_quantity
        }

    def add(self, product_id):
        order = self.get_cart_info()['order']
        product = Product.objects.get(pk=product_id)
        order_product, created = OrderProduct.objects.get_or_create(order=order, product=product)
        if product.quantity > 0:
            order_product.quantity += 1
            product.quantity -= 1
        product.save()
        order_product.save()

    def delete(self, product_id):
        order = self.get_cart_info()['order']
        product = Product.objects.get(pk=product_id)
        order_product, created = OrderProduct.objects.get_or_create(order=order, product=product)

        order_product.quantity -= 1
        product.quantity += 1

        product.save()
        order_product.save()

        if order_product.quantity <= 0:
            order_product.delete()

    def clear(self):
        order = self.get_cart_info()['order']
        for product in order.orderproduct_set.all():
            product.delete()
        order.save()



def get_cart_data(request):
    if request.user.is_authenticated:
        cart = CartForAuthenticatedUser(request)
        cart_info = cart.get_cart_info()
    else:
        session_cart = CartForAnonymousUser(request)
        cart_info = session_cart.get_cart_info()

    order = cart_info['order']
    products = cart_info['products']
    cart_products_quantity = cart_info['cart_products_quantity']

    return {
        'order': order,
        'products': products,
        'cart_products_quantity': cart_products_quantity
    }


def anonymous_order(request, data):
    name = data['name']
    email = data['email']
    phone = data['phone']

    session_cart = CartForAnonymousUser(request)
    cart_info = session_cart.get_cart_info()

    items = cart_info['products']

    customer, created = Customer.objects.get_or_create(
        name=name,
        email=email,
        phone=phone
    )

    customer.save()

    order = Order.objects.create(
        customer=customer,
        complete=False
    )

    for item in items:
        product = Product.objects.get(pk=item['pk'])

        order_product = OrderProduct.objects.create(
            product=product,
            order=order,
            quantity=item['quantity']
        )
    return customer, order
