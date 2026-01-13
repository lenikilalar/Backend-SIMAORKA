from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FinanceTransactionViewSet, Web3PaymentViewSet

router = DefaultRouter()
router.register(r'transactions', FinanceTransactionViewSet)

urlpatterns = [
    path('orgs/<uuid:org_id>/finance/', include([
        path('web3/submit', Web3PaymentViewSet.as_view({'post': 'submit_payment'}), name='web3-submit'),
        path('web3/my-payments', Web3PaymentViewSet.as_view({'get': 'my_payments'}), name='web3-my-payments'),
        path('web3/verify/<uuid:pk>', Web3PaymentViewSet.as_view({'post': 'verify_payment'}), name='web3-verify'),
    ])),
    path('', include(router.urls)),
]
