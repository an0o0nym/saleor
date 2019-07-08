from decimal import Decimal
from typing import Dict

from django import forms
from django.http.request import HttpRequest

from .consts import CALLBACK_SIG_FIELDS, OPERATION_STATUS_COMPLETED, \
    OPERATION_TYPE_PAYMENT
from .utils import compute_sig, auth_payment
from ...interface import PaymentData
from ....payment.models import Transaction, TransactionKind


class DotpayPaymentForm(forms.Form):
    def __init__(self, payment_info: PaymentData, connection_params: Dict,
                 *args, **kwargs):
        kwargs['data'] = kwargs['data'] or {}
        super().__init__(*args, **kwargs)
        self.connection_params = connection_params
        self.payment_info = payment_info

    def get_payment_token(self):
        return auth_payment(self.payment_info, self.connection_params)


class DotpayCallbackForm(forms.Form):
    id = forms.CharField()
    operation_number = forms.CharField()
    operation_type = forms.CharField()
    operation_status = forms.CharField()
    operation_amount = forms.CharField()
    operation_currency = forms.CharField()
    operation_original_amount = forms.CharField()
    operation_original_currency = forms.CharField()
    operation_datetime = forms.CharField()
    operation_related_number = forms.CharField(required=False)
    control = forms.CharField()
    description = forms.CharField()
    email = forms.CharField()
    p_info = forms.CharField()
    p_email = forms.CharField()
    channel = forms.CharField()
    signature = forms.CharField()

    def __init__(self, connection_params: Dict, request: HttpRequest,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_params = connection_params
        self.request = request
        self.payment = None

    def clean_id(self):
        if str(self.cleaned_data['id']) != self.connection_params['id']:
            raise forms.ValidationError("Invalid id")
        return self.cleaned_data['id']

    def clean_operation_type(self):
        if self.cleaned_data['operation_type'] != OPERATION_TYPE_PAYMENT:
            raise forms.ValidationError("Operation invalid type")
        return self.cleaned_data['operation_type']

    def clean_operation_status(self):
        if self.cleaned_data['operation_status'] != OPERATION_STATUS_COMPLETED:
            raise forms.ValidationError("Operation not completed")
        return self.cleaned_data['operation_status']

    def clean(self):
        cleaned_data = super().clean()
        data_copy = cleaned_data.copy()
        del data_copy['signature']

        sig = compute_sig(
            data_copy,
            self.connection_params['pin'],
            CALLBACK_SIG_FIELDS
        )
        if sig != cleaned_data['signature']:
            raise forms.ValidationError("Invalid Signature")

        transaction = Transaction.objects.get(
            payment_id=cleaned_data['control'],
            kind=TransactionKind.AUTH,
            is_success=True,
            amount=cleaned_data['operation_original_amount'],
            currency=cleaned_data['operation_original_currency']
        )
        if not transaction:
            raise forms.ValidationError("Transaction do not exist.")

        self.payment = transaction.payment
        if not self.payment:
            raise forms.ValidationError("Invalid payment")

        if self.payment.total != Decimal(cleaned_data['operation_original_amount']):
            raise forms.ValidationError("Invalid amount")

        if self.payment.currency != cleaned_data['operation_original_currency']:
            raise forms.ValidationError("Invalid amount")
        return cleaned_data

    def get_payment(self):
        return self.payment

    def get_payment_token(self):
        return self.cleaned_data['operation_number']

    def get_order(self):
        return self.payment.order
