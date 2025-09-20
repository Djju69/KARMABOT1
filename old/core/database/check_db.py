from core.database.db import db

# Добавляем категории
db.add_category("🍜 Рестораны")
db.add_category("🧘 SPA")
db.add_category("🚲 Велопрокат")
db.add_category("🏨 Отели")

# Добавляем ресторан
db.add_place(
    name="Hải sản Mộc quán Nha Trang",
    category="🍜 Рестораны",
    address="ул. Морская, Нячанг",
    discount="10%",
    link="https://example.com",
    qr_code="https://example.com/qr.png"
)

# Проверка
print("Категории:")
for cat in db.get_categories():
    print(cat)

print("\nРестораны в категории '🍜 Рестораны':")
for place in db.get_places_by_category("🍜 Рестораны"):
    print(place)
