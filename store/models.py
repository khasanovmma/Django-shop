from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Category(models.Model):

    title = models.CharField(max_length=255, unique=True, verbose_name='Название')

    def get_absolute_url(self):
        return reverse('product_list_by_category', kwargs={'pk': self.pk})

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Product(models.Model):

    name = models.CharField(max_length=200)
    price = models.BigIntegerField()
    image = models.ImageField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категория')
    quantity = models.IntegerField(verbose_name='Количество')
    description = models.TextField(default='Здесь будет описание', verbose_name='Описание')

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Product(pk={self.pk}, category='{self.category}', name='{self.name}')"

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'pk': self.pk})

    @property
    def image_url(self):
        try:
            url = self.image.url
        except:
            url = 'https://www.bbrc.ru/upload/iblock/256/256fb7475b0297cf4c3d2f13fc519372.jpg'
        return url

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'


class Customer(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(max_length=200)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Customer(pk={self.pk}, name='{self.name}', email='{self.email}')"

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'


class Order(models.Model):

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True)
    shipping = models.BooleanField(default=True)

    def __str__(self):
        return str(self.pk)

    @property
    def cart_total_price(self):
        order_products = self.orderproduct_set.all()
        total = sum([product.total_price for product in order_products])
        return total

    @property
    def cart_products_quantity(self):
        order_products = self.orderproduct_set.all()
        total = sum([product.quantity for product in order_products])
        return total


class OrderProduct(models.Model):

    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        total = self.product.price * self.quantity
        return total


class ShippingAddress(models.Model):

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=255, null=False)
    city = models.CharField(max_length=255, null=False)
    state = models.CharField(max_length=255, null=False)
    zipcode = models.CharField(max_length=255, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address
