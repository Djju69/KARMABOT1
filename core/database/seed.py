from db import init_db, add_category, add_restaurant

init_db()

# Добавляем категории (районы)
add_category("Центр", "Center", "중심", "district")
add_category("Север", "North", "북부", "district")

# Добавляем рестораны
add_restaurant(
    name="Hải sản Mộc quán Nha Trang🦞",
    description="Лучшие морепродукты в центре",
    lat=12.23879,
    lon=109.19623,
    category_id=1  # Центр
)
