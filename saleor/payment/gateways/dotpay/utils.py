import base64
import hashlib
from typing import Dict
from urllib import parse

import requests
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext as _
from django_countries import data as dj_countries_data

from .consts import ONLINE_SIG_FIELDS
from ...interface import PaymentData
from ....order.models import Order
from ....payment.models import Payment


def encode_param(param):
    return str(param).encode('unicode-escape').decode()


def process_params(params, flatten=True):
    new_params = dict()
    for k, v in params.items():
        if v is None or v == '':
            continue

        if isinstance(v, dict):
            v = process_params(v, flatten)
            if flatten:
                new_params.update(v)
                continue

            new_params[k] = v
            continue

        new_params[k] = encode_param(v)
    return new_params


def compute_sig(params, pin):
    params = process_params(params)
    text = pin + ("".join(map(lambda field: str(params.get(field, '')), ONLINE_SIG_FIELDS)))
    return hashlib.sha256(text.encode('utf8')).hexdigest()


def gen_credentials(connection_params: Dict) -> str:
    credentials = ":".join([connection_params['username'], connection_params['password']])
    return base64.b64encode(credentials.encode()).decode()


def get_country_alt_code(country_code):
    if country_code not in dj_countries_data.ALT_CODES:
        return country_code
    return dj_countries_data.ALT_CODES[country_code][0]


def gen_url(request: HttpRequest, payment_info: PaymentData = None, order: Order = None):
    if not order:
        order = Order.objects.get(id=payment_info.order_id)
    return request.build_absolute_uri(reverse("order:payment-success", kwargs={"token": order.token}))


def gen_data(payment_info: PaymentData, connection_params: Dict, request: HttpRequest) -> Dict:
    order = Order.objects.get(id=payment_info.order_id)
    payer_data = payment_info.billing
    description = _("Order id: %s") % payment_info.order_id

    data = dict(
        amount=str(payment_info.amount),
        currency=payment_info.currency,
        description=description,
        control=str(payment_info.order_id),
        language=order.language_code,
        ignore_last_payment_channel=str(connection_params['ignore_last_chnl']),
        redirection_type=str(connection_params['type']),
        url=gen_url(request, order=order),
        urlc=None,
        payer=dict(
            first_name=payer_data.first_name,
            last_name=payer_data.last_name,
            email=payment_info.customer_email,
            phone=payer_data.phone,
            address=dict(
                street=', '.join([payer_data.street_address_1, payer_data.street_address_2]),
                postcode=payer_data.postal_code,
                city=payer_data.city,
                region=payer_data.country_area,
                country=get_country_alt_code(payer_data.country)
            )
        )
    )
    return process_params(data, flatten=False)


def gen_pid(payment_info: PaymentData, connection_params: Dict, request: HttpRequest) -> str:
    url = parse.urljoin(connection_params['seller_url'], 'accounts/%s/payment_links/')
    data = gen_data(payment_info, connection_params, request)
    headers = {
        'Authorization': 'Basic %s' % gen_credentials(connection_params),
        'Content-type': 'application/json',
        'Accept': 'application/json'
    }

    resp = requests.post(url % connection_params['id'], json=data, headers=headers)
    token = resp.json()['token']

    payment = Payment.objects.get(pk=payment_info.payment_id)
    payment.token = token
    payment.save(update_fields=['token'])

    return token
