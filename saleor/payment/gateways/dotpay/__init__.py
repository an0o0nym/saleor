import logging
import urllib.parse as urlparse
from typing import Dict

from django.http.request import HttpRequest

from .consts import ONLINE_SIG_FIELDS
from .forms import DotpayPaymentForm, DotpayCallbackForm
from .utils import auth_payment
from .utils import compute_sig
from ...interface import PaymentData, GatewayConfig, GatewayResponse
from ....payment import TransactionKind
from ....payment.models import Payment

logger = logging.getLogger(__name__)


def create_form(
        data: Dict,
        payment_information: PaymentData,
        connection_params: Dict
) -> DotpayPaymentForm:
    return DotpayPaymentForm(payment_information, connection_params, data=data)


def get_client_token(config: GatewayConfig) -> str:
    return ''


def get_callback_codes():
    positive_code = 200
    negative_code = 500
    return positive_code, negative_code


def get_callback_contents():
    positive_content = 'OK'
    negative_content = 'ERROR'
    return positive_content, negative_content


def create_callback_form(
    connection_params: Dict,
    request: HttpRequest,
    data: Dict
) -> DotpayCallbackForm:
    return DotpayCallbackForm(connection_params, request, data=data)


def capture(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    return GatewayResponse(
        is_success=True,
        kind=TransactionKind.CAPTURE,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token,
        error=None,
    )


def authorize(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    payment = Payment.objects.get(pk=payment_information.payment_id)
    payment.token = payment_information.token
    payment.save(update_fields=['token'])

    return GatewayResponse(
        is_success=True,
        kind=TransactionKind.AUTH,
        amount=payment_information.amount,
        currency=payment_information.currency,
        transaction_id=payment_information.token,
        error=None,
    )


def get_manual_action_url(payment: Payment, connection_params: Dict) -> str:
    payment.refresh_from_db()
    params = {
        'pid': payment.token,
        'chk': compute_sig(
            {'pid': payment.token},
            connection_params['pin'],
            ONLINE_SIG_FIELDS
        )
    }
    return '%s?%s' % (connection_params['payment_url'], urlparse.urlencode(params))


def process_payment(
    payment_information: PaymentData, config: GatewayConfig
) -> GatewayResponse:
    return authorize(payment_information=payment_information, config=config)
