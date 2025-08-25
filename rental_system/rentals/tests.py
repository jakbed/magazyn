from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Category, Product, Order, BorrowHistory


class OrderCreationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='john', password='pass', email='john@example.com')
        self.category = Category.objects.create(name='Camera')
        self.product = Product.objects.create(brand='Canon', model='X1', category=self.category)

    def test_order_creation_updates_product_status_and_creates_history(self):
        self.client.login(username='john', password='pass')
        response = self.client.post(reverse('rentals:order_create'), {
            'conference_code': 'CONF123',
            'products': [self.product.pk],
            'komplets': [],
            'pickup_date': '2023-01-01',
            'return_date': '2023-01-10',
        })
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, 'wyjazd')
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.user, self.user)
        self.assertEqual(BorrowHistory.objects.filter(user=self.user, product=self.product).count(), 1)


class ServiceViewTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.category = Category.objects.create(name='Lights')
        self.product = Product.objects.create(brand='Philips', model='L1', category=self.category)

    def test_service_creation_changes_product_status(self):
        self.client.login(username='staff', password='pass')
        response = self.client.post(reverse('rentals:service_create'), {
            'product': self.product.pk,
            'description': 'Broken',
        })
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.status, 'serwis')


class LoginRequiredViewTests(TestCase):
    def setUp(self):
        self.url = reverse('rentals:product_list')
        self.user = User.objects.create_user(username='alice', password='pass')

    def test_redirect_when_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_access_when_logged_in(self):
        self.client.login(username='alice', password='pass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
