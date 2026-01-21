from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FinanceTransactionViewSet, Web3PaymentViewSet, FinanceSummaryView,
    PublicFinanceView, PublicFinanceTransactionsView
)

router = DefaultRouter()
router.register(r'transactions', FinanceTransactionViewSet)

urlpatterns = [
    # Org-scoped finance (authenticated)
    path('orgs/<uuid:org_id>/finance/', include([
        path('summary', FinanceSummaryView.as_view(), name='finance-summary'),
        path('web3/submit', Web3PaymentViewSet.as_view({'post': 'submit_payment'}), name='web3-submit'),
        path('web3/my-payments', Web3PaymentViewSet.as_view({'get': 'my_payments'}), name='web3-my-payments'),
        path('web3/payments', Web3PaymentViewSet.as_view({'get': 'all_payments'}), name='web3-all-payments'),
        path('web3/verify/<uuid:pk>', Web3PaymentViewSet.as_view({'post': 'verify_payment'}), name='web3-verify'),
    ])),
    
    # Public finance transparency (no auth required)
    path('organizations/<slug:slug>/finance/public', PublicFinanceView.as_view(), name='public-finance'),
    path('organizations/<slug:slug>/finance/public/transactions', PublicFinanceTransactionsView.as_view(), name='public-finance-transactions'),
    
    path('', include(router.urls)),
]
