from typing import Dict

from django import forms

from .utils import gen_pid, compute_sig
from ...interface import PaymentData
from django.http.request import HttpRequest


class DotpayPaymentForm(forms.Form):
    pid = forms.CharField(widget=forms.HiddenInput)
    chk = forms.CharField(widget=forms.HiddenInput)

    def __init__(self, payment_info: PaymentData, connection_params: Dict,
                 request: HttpRequest, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_params = connection_params
        self.payment_info = payment_info

        pid = gen_pid(self.payment_info, self.connection_params, request)
        self.initial.update({
            'pid': pid,
            'chk': compute_sig({'pid': pid}, self.connection_params['pin'])
        })

    @property
    def action(self):
        return self.connection_params['payment_url']
