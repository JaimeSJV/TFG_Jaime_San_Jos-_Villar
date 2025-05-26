from django import forms
from .models import Cuad


class CuadForm(forms.ModelForm):
    class Meta:
        model = Cuad
        fields = ['Imagen_cuadricula']