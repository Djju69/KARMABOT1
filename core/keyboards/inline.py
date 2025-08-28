from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton   

# Inline-клавиатура выбора ресторана (пример)
select_restoran = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Hải sản Mộc quán Nha Trang🦞", callback_data="restoran_2_10_1_0"),
            InlineKeyboardButton(text="Тест рест", callback_data="restoran_2_10_1_1")
        ],
        [
            InlineKeyboardButton(text="Выбор ресторана по районам🌆", callback_data="rests_by_district"),
            InlineKeyboardButton(text="Показать ближайшие 📍", callback_data="rest_near_me")
        ]
    ],
    row_width=2
)

# Inline-клавиатура региональных ресторанов (пример, можно расширять)
regional_restoran = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Район 1", callback_data="district_1"),
            InlineKeyboardButton(text="Район 2", callback_data="district_2")
        ]
    ],
    row_width=2
)

# Inline-клавиатура выбора кухни (новая клавиатура)
kitchen_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Вьетнамская кухня", callback_data="kitchen_vietnamese"),
            InlineKeyboardButton(text="Японская кухня", callback_data="kitchen_japanese")
        ],
        [
            InlineKeyboardButton(text="Итальянская кухня", callback_data="kitchen_italian"),
            InlineKeyboardButton(text="Французская кухня", callback_data="kitchen_french")
        ]
    ],
    row_width=2
)

# Inline-клавиатура для скидок (добавлена, чтобы убрать ошибку импорта)
discount_generator = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Получить скидку 10%", callback_data="discount_10"),
            InlineKeyboardButton(text="Получить скидку 20%", callback_data="discount_20")
        ]
    ],
    row_width=2
)

# ===== Новый вариант: Inline-клавиатура выбора языка для callback =====
language_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton(text="🇰🇷 한국어", callback_data="lang_ko")
        ]
    ]
)

# ===== Старый вариант: Reply клавиатура выбора языка =====
# language_keyboard = ReplyKeyboardMarkup(
#     keyboard=[
#         [
#             KeyboardButton(text="🇷🇺 Русский"),
#             KeyboardButton(text="🇬🇧 English"),
#             KeyboardButton(text="🇰🇷 한국어")
#         ]
#     ],
#     resize_keyboard=True,
#     one_time_keyboard=True
# )
