from django import template
from store.models import Category
from store.utils import get_cart_data

register = template.Library()


@register.simple_tag()
def get_categories():
    return Category.objects.all()


@register.simple_tag()
def get_sorters():

    info = [
        {
            'title': 'По цене',
            'sorters': [
                ('price', 'По возрастанию'),
                ('-price', 'По убыванию')
            ]
        },
        {
            'title': 'По дате добавления',
            'sorters': [
                ('created_at', 'Сначала старые'),
                ('-created_at', 'Сначала новые'),
            ]
        },
        {
            'title': 'По названию',
            'sorters': [
                ('name', 'от А до Я'),
                ('-name', 'от Я до А')
            ]
        },
    ]
    return info


@register.simple_tag()
def get_cart_total_quantity(request):
    data = get_cart_data(request)
    return data['cart_products_quantity']
