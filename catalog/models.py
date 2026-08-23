from django.db import models

class Item(models.Model):

    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_soldout = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.price}) [{'Sold Out' if self.is_soldout else 'Available'}]"


