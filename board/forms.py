from django import forms
from .models import Equipment
class RequestForm(forms.Form):
    equipment = forms.ModelChoiceField(queryset=Equipment.objects.filter(active=True))
    start = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    purpose = forms.CharField(max_length=240, widget=forms.Textarea(attrs={"rows": 2, "placeholder": "What are you planning?"}))
class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = ["name", "category", "description"]
