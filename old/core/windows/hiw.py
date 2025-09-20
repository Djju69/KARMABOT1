from aiogram.types import Message
from aiogram import Bot

def hiw_text(lang: str = 'ru') -> str:
    """Возвращает текст 'Как это работает' на указанном языке."""
    texts = {
        'ru': '''Как это работает:
1. Выбираете услугу
2. Показываете QR-код   <b>ПЕРЕД тем, как сделаете заказ</b>
3. Получаете скидку''',
        'en': '''How it works:
1. Choose a service
2. Show QR code   <b>BEFORE you place your order</b>
3. Get discount''',
        'vi': '''Cách hoạt động:
1. Chọn dịch vụ
2. Hiển thị mã QR   <b>TRƯỚC KHI bạn đặt hàng</b>
3. Nhận giảm giá''',
        'ko': '''작동 방식:
1. 서비스 선택
2. QR 코드 표시   <b>주문하기 전에</b>
3. 할인 받기'''
    }
    return texts.get(lang, texts['ru'])