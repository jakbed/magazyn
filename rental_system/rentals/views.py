from django.shortcuts import render

# Create your views here.
# rentals/views.py (fragment z widokami API)
from rest_framework import viewsets, permissions
from .models import Category, Product, Komplet, Order, BorrowHistory, Serwis, Service, UserProfile
from .serializers import (
    CategorySerializer, ProductSerializer, KompletSerializer, OrderSerializer,
    BorrowHistorySerializer, SerwisSerializer, ServiceSerializer, UserProfileSerializer)
from django.contrib.auth.models import User
from .forms import ProfileForm


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]  # wymagana autentykacja

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

class KompletViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Komplet.objects.all()
    serializer_class = KompletSerializer
    permission_classes = [permissions.IsAuthenticated]

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

class BorrowHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BorrowHistory.objects.select_related('user', 'product', 'komplet').all()
    serializer_class = BorrowHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

class SerwisViewSet(viewsets.ModelViewSet):
    queryset = Serwis.objects.all()
    serializer_class = SerwisSerializer
    permission_classes = [permissions.IsAdminUser]  # tylko admin

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related('product','komplet','serwis').all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]



# rentals/views.py (ciąg dalszy)
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.utils import timezone
from .models import Product, Komplet, Order, BorrowHistory, Service, UserProfile

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'rentals/product_list.html'
    context_object_name = 'products'
    paginate_by = 10  # paginacja 10 na stronę (opcjonalnie)
    queryset = Product.objects.filter(status='magazyn')  # domyślnie pokazuj tylko dostępne

class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'rentals/product_detail.html'
    context_object_name = 'product'

class KompletListView(LoginRequiredMixin, ListView):
    model = Komplet
    template_name = 'rentals/komplet_list.html'
    context_object_name = 'komplets'
    paginate_by = 10
    queryset = Komplet.objects.filter(status='magazyn')

class KompletDetailView(LoginRequiredMixin, DetailView):
    model = Komplet
    template_name = 'rentals/komplet_detail.html'
    context_object_name = 'komplet'

# Formularz wypożyczenia (Order) – użyjemy CreateView, ale musimy nadpisać pewne zachowania
class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    fields = ['conference_code', 'products', 'komplets', 'pickup_date', 'return_date']  # pola w formularzu
    template_name = 'rentals/order_form.html'
    success_url = reverse_lazy('rentals:dashboard')  # po złożeniu zamówienia, przejdź na dashboard

    def get_form(self, *args, **kwargs):
        """Dostosowanie formularza: ograniczenie listy produktów/kompletów do dostępnych oraz ustawienie widgetów."""
        form = super().get_form(*args, **kwargs)
        # Ograniczamy wybór produktów/kompletów do dostępnych (status=magazyn)
        form.fields['products'].queryset = Product.objects.filter(status='magazyn')
        form.fields['komplets'].queryset = Komplet.objects.filter(status='magazyn')
        # Ustawiamy atrybut HTML multiple dla pola produktów i kompletów (wielokrotny wybór)
        form.fields['products'].widget.attrs.update({'class': 'form-select', 'multiple': 'multiple'})
        form.fields['komplets'].widget.attrs.update({'class': 'form-select', 'multiple': 'multiple'})
        # Opcjonalnie można ustawić pola daty jako type=date
        form.fields['pickup_date'].widget.attrs.update({'type': 'date', 'class': 'form-control'})
        form.fields['return_date'].widget.attrs.update({'type': 'date', 'class': 'form-control'})
        form.fields['conference_code'].widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        """Automatyczne przypisanie użytkownika do zamówienia i sprawdzenie dostępności sprzętu."""
        form.instance.user = self.request.user  # przypisz zalogowanego użytkownika
        # Sprawdź czy wybrane produkty/komplety są dostępne (nadal w magazynie)
        selected_products = form.cleaned_data.get('products')
        selected_komplets = form.cleaned_data.get('komplets')
        for prod in selected_products:
            if prod.status != 'magazyn':
                form.add_error('products', f"Produkt {prod} nie jest dostępny do wypożyczenia.")
        for komp in selected_komplets:
            if komp.status != 'magazyn':
                form.add_error('komplets', f"Komplet {komp} nie jest dostępny do wypożyczenia.")
        if form.errors:
            return self.form_invalid(form)  # jeśli wykryto błędy dostępności, przerwij zapisywanie
        # Zapisz zamówienie
        response = super().form_valid(form)  # to utworzy obiekt Order i zapisze powiązania M2M
        order = self.object  # nowo utworzone zamówienie
        # Aktualizuj statusy produktów i kompletów na "wyjazd" oraz zarejestruj historię wypożyczenia
        for prod in order.products.all():
            prod.status = 'wyjazd'
            prod.save()
            BorrowHistory.objects.create(user=self.request.user, product=prod, borrow_date=timezone.now())
        for komp in order.komplets.all():
            komp.status = 'wyjazd'
            komp.save()
            BorrowHistory.objects.create(user=self.request.user, komplet=komp, borrow_date=timezone.now())
        # Wysłanie potwierdzenia e-mail do użytkownika
        self.send_confirmation_email(order)
        return response

    def send_confirmation_email(self, order):
        """Wysyła e-mail potwierdzający złożenie zamówienia."""
        user_email = order.user.email
        if not user_email:
            return
        subject = "Potwierdzenie wypożyczenia sprzętu"
        body = (f"Dziękujemy za złożenie wypożyczenia.\n\n"
                f"Kod konferencji: {order.conference_code}\n"
                f"Wypożyczone produkty: {', '.join(str(p) for p in order.products.all())}\n"
                f"Wypożyczone komplety: {', '.join(str(k) for k in order.komplets.all())}\n"
                f"Planowana data odbioru: {order.pickup_date}\n"
                f"Planowana data zwrotu: {order.return_date}\n\n"
                f"Prosimy o terminowy zwrot sprzętu. \nPozdrawiamy,\nZespół Wypożyczalni")
        from django.conf import settings
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user_email], fail_silently=True)

class UserDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "rentals/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        # Aktywne wypożyczenia: zamówienia, które nie są oznaczone jako zwrócone
        ctx['active_orders'] = Order.objects.filter(user=user).exclude(status='returned').order_by('-reserved_at')
        # Historia wypożyczeń (zakończone)
        ctx['past_orders'] = Order.objects.filter(user=user, status='returned').order_by('-return_date')
        # Profil użytkownika
        ctx['profile'] = user.profile  # dzięki related_name 'profile' w UserProfile
        return ctx

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'rentals/profile_form.html'
    success_url = reverse_lazy('rentals:dashboard')

    def get_object(self):
        return self.request.user


# Widok zgłoszenia serwisowego – dostępny tylko dla personelu (staff)
class ServiceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Service
    fields = ['product', 'komplet', 'description', 'serwis']
    template_name = "rentals/service_form.html"
    success_url = reverse_lazy('rentals:product_list')

    def test_func(self):
        # Tylko użytkownik z uprawnieniami pracownika (staff) może dodawać zgłoszenia serwisowe
        return self.request.user.is_staff

    def form_valid(self, form):
        # Przy zgłoszeniu usterki, zmień status produktu/kompletu na "serwis"
        response = super().form_valid(form)
        service = self.object
        if service.product:
            service.product.status = 'serwis'
            service.product.save()
        if service.komplet:
            service.komplet.status = 'serwis'
            service.komplet.save()
        return response

class KompletListView(ListView):
    model = Komplet
    template_name = 'rentals/komplet_list.html'
    context_object_name = 'komplets'
