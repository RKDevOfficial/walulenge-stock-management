from django.contrib import admin
from .models import (
    Sale,
    SaleItem,
    SalePayment,
    BicycleFrameSale,
    BicycleFramePayment,
)


admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(SalePayment)
admin.site.register(BicycleFrameSale)
admin.site.register(BicycleFramePayment)
