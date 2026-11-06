from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Category, Product
from .views import generate_product_code


class ProductCodeGenerationTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Engine Parts')
        self.manager = User.objects.create_user(
            username='manager',
            password='test-password',
            role=User.Role.MANAGER,
        )

    def create_product(self, category, product_code):
        return Product.objects.create(
            category=category,
            name='Test product',
            product_code=product_code,
            buying_price='10.00',
            retail_price='20.00',
            wholesale_price='15.00',
        )

    def test_code_sequence_is_category_specific(self):
        self.assertEqual(generate_product_code(self.category), 'WAS-ENGPAR-0001')
        self.create_product(self.category, 'WAS-ENGPAR-0001')
        self.assertEqual(generate_product_code(self.category), 'WAS-ENGPAR-0002')

        other_category = Category.objects.create(name='Body')
        self.assertEqual(generate_product_code(other_category), 'WAS-BOD-0001')

    def test_create_generates_code_when_code_is_blank(self):
        self.client.force_login(self.manager)

        response = self.client.post(reverse('product_create'), {
            'name': 'New product',
            'product_code': '',
            'category': self.category.pk,
            'buying_price': '10.00',
            'retail_price': '20.00',
            'wholesale_price': '15.00',
        })

        self.assertRedirects(response, reverse('product_list'))
        product = Product.objects.get(name='New product')
        self.assertEqual(product.product_code, 'WAS-ENGPAR-0001')

    def test_create_preserves_manufacturer_code(self):
        self.client.force_login(self.manager)

        response = self.client.post(reverse('product_create'), {
            'name': 'New product',
            'product_code': 'MFR-12345',
            'category': self.category.pk,
            'buying_price': '10.00',
            'retail_price': '20.00',
            'wholesale_price': '15.00',
        })

        self.assertRedirects(response, reverse('product_list'))
        product = Product.objects.get(name='New product')
        self.assertEqual(product.product_code, 'MFR-12345')
