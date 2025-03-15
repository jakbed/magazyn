# rentals/models.py
from django.db import models
from django.contrib.auth.models import User  # używamy wbudowanego modelu użytkownika
from django.db.models.signals import post_save
from django.dispatch import receiver

# Definicja dostępnych statusów dla produktu/kompletu
STATUS_CHOICES = [
    ('magazyn', 'Magazyn'),       # dostępny w magazynie
    ('wyjazd', 'Wyjazd'),         # aktualnie wypożyczony (w użyciu)
    ('serwis', 'Serwis'),         # zablokowany, w naprawie
    ('odrzucone', 'Odrzucone'),   # wycofany z użytku
]

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    brand = models.CharField(max_length=100)        # marka
    model = models.CharField(max_length=100)        # model
    code = models.CharField(max_length=50, unique=True, null=True, editable=False)   # unikatowy kod produktu

    def save(self, *args, **kwargs):
        # If the object is new and has no ID yet, save it to generate an ID first
        if not self.id:
            super().save(*args, **kwargs)
            # Generate the product code using brand, model, and the newly generated ID
            self.code = f"{self.brand}_{self.model}_{self.id}"
            # Save again to update the code field (use update_fields to avoid recursion)
            super().save(update_fields=["code"])
        else:
            # If updating an existing object, proceed with normal save
            super().save(*args, **kwargs)

    serial_number = models.CharField(max_length=100, blank=True, null=True)  # numer seryjny
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='magazyn')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', default="null")
    quantity = models.PositiveIntegerField(default=1)    # ilość sztuk (jeśli dotyczy)
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)  # waga w kg
    ean_code = models.CharField(max_length=13, blank=True, null=True)  # kod EAN
    image = models.ImageField(upload_to='products/', blank=True, null=True)  # zdjęcie produktu

    def __str__(self):
        return f"{self.brand} {self.model} ({self.code})"

class Komplet(models.Model):
    name = models.CharField(max_length=100, unique=True)
    products = models.ManyToManyField(Product, related_name='komplets')  # lista produktów wchodzących w skład kompletu
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='magazyn')
    # Historia wypożyczeń kompletu będzie śledzona w modelu BorrowHistory (powiązanie przez pole 'komplet')

    def __str__(self):
        return f"Komplet: {self.name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('reserved', 'Zarezerwowane'),   # złożona rezerwacja (oczekuje na odbiór)
        ('ongoing', 'Wypożyczone'),      # w trakcie wypożyczenia (odebrane przez użytkownika)
        ('returned', 'Zwrócone'),        # zakończone, sprzęt zwrócony
        ('canceled', 'Anulowane'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    conference_code = models.CharField(max_length=50)  # kod konferencji (wymagany przy wypożyczeniu)
    products = models.ManyToManyField(Product, blank=True, related_name='orders')
    komplets = models.ManyToManyField(Komplet, blank=True, related_name='orders')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='reserved')
    reserved_at = models.DateTimeField(auto_now_add=True)  # data rezerwacji
    pickup_date = models.DateField(null=True, blank=True)  # planowana data odbioru
    return_date = models.DateField(null=True, blank=True)  # planowana data zwrotu

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} ({self.status})"

class BorrowHistory(models.Model):
    """ Historia wypożyczeń poszczególnych produktów i kompletów """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    komplet = models.ForeignKey(Komplet, on_delete=models.CASCADE, null=True, blank=True)
    borrow_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        item = self.product or self.komplet  # który obiekt został wypożyczony
        return f"{item} wypożyczony przez {self.user.username} w dniu {self.borrow_date.date()}"

class Serwis(models.Model):
    """ Zewnętrzny serwis naprawczy """
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    street = models.CharField(max_length=255, null=True)
    number = models.CharField(max_length=10, null=True)
    postal_code = models.CharField(max_length=10, null=True)
    city = models.CharField(max_length=100, null=True)
    country = models.CharField(max_length=100, default='Polska')

    def __str__(self):
        return self.name

class Service(models.Model):
    """ Zgłoszenie serwisowe dla produktu lub kompletu """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    komplet = models.ForeignKey(Komplet, on_delete=models.CASCADE, null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)    # data zgłoszenia usterki
    description = models.TextField()                         # opis usterki
    serwis = models.ForeignKey(Serwis, on_delete=models.SET_NULL, null=True, blank=True)  # serwis naprawczy (opcjonalnie)
    resolved = models.BooleanField(default=False)            # czy naprawa zakończona
    resolved_at = models.DateTimeField(null=True, blank=True)  # data zakończenia naprawy

    def __str__(self):
        item = self.product or self.komplet
        return f"Zgłoszenie serwisowe: {item} ({'naprawione' if self.resolved else 'w toku'})"

class UserProfile(models.Model):
    """ Profil użytkownika rozszerzający wbudowany model User """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)  # zdjęcie profilowe

    def __str__(self):
        return f"Profil: {self.user.username}"



@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
