from logging import getLogger
import json

import razorpay
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, mixins, viewsets

from api.models import Order
from api.models.payment import Package
from api.serializers.payment import PackageSerializer

logger = getLogger(__name__)
rzp_client = razorpay.Client(
    auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET)
)


class VerifyPayment(APIView):
    def post(self, request, version, format=None):
        error = None
        response = {}
        try:
            data = json.loads(request.body)
        except Exception as ex:
            logger.exception(ex)
            error = "Error parsing Payload"
        else:
            generic_error = "could not verify signature!"
            order_id = data.get("razorpay_order_id")
            try:
                order = Order.objects.get(order_id=order_id)
            except Order.DoesNotExist:
                error = generic_error
            else:
                try:
                    rzp_client.utility.verify_payment_signature(data)
                except Exception as ex:
                    logger.exception(ex)
                    error = generic_error
                else:
                    rzp_payment_id = data["razorpay_payment_id"]
                    order.payment_id = rzp_payment_id
                    order.save()
                    # send_film_registration_email(request.user, order)
                    response["detail"] = "Payment Complete"

        response["success"] = False if error else True
        if error:
            response["detail"] = error
        status_code = status.HTTP_400_BAD_REQUEST if error else status.HTTP_200_OK
        return Response(response, status=status_code)


class PackageView(mixins.ListModelMixin, viewsets.GenericViewSet):

    queryset = Package.objects.all()
    filterset_fields = ["active"]
    serializer_class = PackageSerializer
