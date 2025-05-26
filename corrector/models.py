from django.db import models

# Create your models here.
class Cuad(models.Model):
    Imagen_cuadricula = models.ImageField(upload_to='images/')