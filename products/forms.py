from django import forms

from .models import Product, Supplier


class ProductForm(forms.ModelForm):
    product_code = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Leave blank to generate automatically',
        })
    )
    suppliers = forms.ModelMultipleChoiceField(
        queryset=Supplier.objects.order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['product_code'].required = True

    class Meta:
        model = Product
        fields = (
            'name',
            'product_code',
            'category',
            'description',
            'buying_price',
            'retail_price',
            'wholesale_price',
            'suppliers',
            'image',
            'is_available',
        )
