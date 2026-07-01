import crcmod
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile


def _crc16(payload: str) -> str:
    crc16_func = crcmod.mkCrcFun(0x11021, rev=True, initCrc=0xFFFF, xorOut=0x0000)
    crc = crc16_func(payload.encode("ascii") + b"6304")
    return f"{crc:04X}"


def _format_value(value: str, tag: str) -> str:
    size = f"{len(value):02d}"
    return f"{tag}{size}{value}"


def generate_pix_payload(key: str, merchant_name: str, merchant_city: str, amount: float, txid: str = "***") -> str:
    name = merchant_name[:25]
    city = merchant_city[:15]
    amount_str = f"{amount:.2f}"

    payload = "000201"
    payload += _format_value("0014br.gov.bcb.pix" + _format_value(key, "01"), "26")
    payload += _format_value("BR", "52")
    payload += _format_value(amount_str, "54")
    payload += _format_value(name, "59")
    payload += _format_value(city, "60")
    payload += _format_value(_format_value(txid, "05"), "62")
    payload += "6304" + _crc16(payload)

    return payload


def generate_pix_qr_code(payload: str) -> BytesIO:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generate_pix(key: str, merchant_name: str, merchant_city: str, amount: float) -> dict:
    payload = generate_pix_payload(key, merchant_name, merchant_city, amount)
    qr_image = generate_pix_qr_code(payload)
    return {
        "payload": payload,
        "qr_image": qr_image,
    }


def generate_pix_for_order(order) -> dict:
    restaurant = order.restaurant
    return generate_pix(
        key=restaurant.pix_key,
        merchant_name=restaurant.merchant_name or restaurant.name,
        merchant_city=restaurant.merchant_city,
        amount=float(order.total),
    )
