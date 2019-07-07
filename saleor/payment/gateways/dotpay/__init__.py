import logging
from typing import Dict

from django.http.request import HttpRequest

from .forms import DotpayPaymentForm
from .utils import gen_pid
from ...interface import PaymentData, GatewayConfig

logger = logging.getLogger(__name__)


def create_form(
        data: Dict,
        payment_information: PaymentData,
        connection_params: Dict,
        request: HttpRequest
) -> DotpayPaymentForm:
    return DotpayPaymentForm(payment_information, connection_params, request)


def get_client_token(config: GatewayConfig) -> str:
    return ''
