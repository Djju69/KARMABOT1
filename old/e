[1mdiff --git a/core/handlers/ai_help.py b/core/handlers/ai_help.py[m
[1mindex 6b1f278..4f88a6c 100644[m
[1m--- a/core/handlers/ai_help.py[m
[1m+++ b/core/handlers/ai_help.py[m
[36m@@ -90,6 +90,12 @@[m [mdef create_help_menu_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:[m
             callback_data="help:contact_support"[m
         )[m
     )[m
[32m+[m[32m    builder.row([m
[32m+[m[32m        InlineKeyboardButton([m
[32m+[m[32m            text=texts.get('btn.tariffs', '🏢 Тарифы'),[m
[32m+[m[32m            callback_data="help:tariffs"[m
[32m+[m[32m        )[m
[32m+[m[32m    )[m
     builder.row([m
         InlineKeyboardButton([m
             text=texts.get('btn.back', '◀️ Назад'),[m
[36m@@ -460,6 +466,53 @@[m [masync def back_to_help_menu(callback: CallbackQuery, state: FSMContext):[m
     except Exception as e:[m
         logger.error(f"Error going back: {e}", exc_info=True)[m
 [m
[32m+[m[32m# Обработчик кнопки "Тарифы"[m
[32m+[m[32m@ai_help_router.callback_query(F.data == "help:tariffs")[m
[32m+[m[32masync def show_tariffs(callback: CallbackQuery, state: FSMContext):[m
[32m+[m[32m    """Показать страницу тарифов"""[m
[32m+[m[32m    try:[m
[32m+[m[32m        user_id = callback.from_user.id[m
[32m+[m[32m        lang = await get_user_lang(user_id)[m
[32m+[m[32m        texts = get_all_texts(lang)[m
[32m+[m[41m        [m
[32m+[m[32m        logger.info(f"[AI_HELP] Tariffs requested by user {user_id}")[m
[32m+[m[41m        [m
[32m+[m[32m        # Создаем WebApp URL для тарифов[m
[32m+[m[32m        from core.services.webapp_integration import create_webapp_url[m
[32m+[m[32m        webapp_url = create_webapp_url(user_id, '/tariffs.html')[m
[32m+[m[41m        [m
[32m+[m[32m        tariff_text = texts.get('help.tariffs',[m
[32m+[m[32m            "🏢 **Тарифы KARMABOT1**\n\n"[m
[32m+[m[32m            "Выберите подходящий тариф для вашего бизнеса:\n\n"[m
[32m+[m[32m            "🆓 **FREE STARTER** - 0 VND/мес, 12% комиссия, до 15 транзакций\n"[m
[32m+[m[32m            "💼 **BUSINESS** - 490,000 VND/мес, 6% комиссия, до 100 транзакций\n"[m
[32m+[m[32m            "🏢 **ENTERPRISE** - 960,000 VND/мес, 4% комиссия, безлимит\n\n"[m
[32m+[m[32m            "Нажмите кнопку ниже для просмотра детальной информации:"[m
[32m+[m[32m        )[m
[32m+[m[41m        [m
[32m+[m[32m        keyboard = InlineKeyboardMarkup(inline_keyboard=[[m
[32m+[m[32m            [InlineKeyboardButton([m
[32m+[m[32m                text=texts.get('btn.view_tariffs', '🏢 Посмотреть тарифы'),[m
[32m+[m[32m                web_app=WebAppInfo(url=webapp_url)[m
[32m+[m[32m            )],[m
[32m+[m[32m            [InlineKeyboardButton([m
[32m+[m[32m                text=texts.get('btn.back', '◀️ Назад'),[m
[32m+[m[32m                callback_data="help:back"[m
[32m+[m[32m            )][m
[32m+[m[32m        ])[m
[32m+[m[41m        [m
[32m+[m[32m        await callback.message.edit_text([m
[32m+[m[32m            tariff_text,[m
[32m+[m[32m            reply_markup=keyboard,[m
[32m+[m[32m            parse_mode="HTML"[m
[32m+[m[32m        )[m
[32m+[m[41m        [m
[32m+[m[32m        await callback.answer()[m
[32m+[m[41m        [m
[32m+[m[32m    except Exception as e:[m
[32m+[m[32m        logger.error(f"Error showing tariffs: {e}", exc_info=True)[m
[32m+[m[32m        await callback.answer("❌ Ошибка при загрузке тарифов", show_alert=True)[m
[32m+[m
 # Обработчик возврата в главное меню[m
 @ai_help_router.callback_query(F.data == "help:main_menu")[m
 async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):[m
[1mdiff --git a/core/handlers/webapp_handler.py b/core/handlers/webapp_handler.py[m
[1mindex a45cb66..8769e08 100644[m
[1m--- a/core/handlers/webapp_handler.py[m
[1m+++ b/core/handlers/webapp_handler.py[m
[36m@@ -64,6 +64,29 @@[m [masync def handle_webapp_data(message: Message):[m
                 f"• Сохранение данных в браузере",[m
                 parse_mode="HTML"[m
             )[m
[32m+[m[41m        [m
[32m+[m[32m        elif action == 'change_language':[m
[32m+[m[32m            # Изменение языка пользователя[m
[32m+[m[32m            language = data.get('language', 'ru')[m
[32m+[m[32m            logger.info(f"[WEBAPP] Language change request from user {user_id}: {language}")[m
[32m+[m[41m            [m
[32m+[m[32m            # Обновляем язык пользователя в БД[m
[32m+[m[32m            from core.services.translation_service import translation_service[m
[32m+[m[32m            success = translation_service.set_user_language(user_id, language)[m
[32m+[m[41m            [m
[32m+[m[32m            if success:[m
[32m+[m[32m                await message.answer([m
[32m+[m[32m                    f"✅ <b>Язык изменен!</b>\n\n"[m
[32m+[m[32m                    f"Интерфейс переключен на: {translation_service.get_language_name(language)}\n\n"[m
[32m+[m[32m                    f"Изменения вступят в силу при следующем открытии кабинета.",[m
[32m+[m[32m                    parse_mode="HTML"[m
[32m+[m[32m                )[m
[32m+[m[32m            else:[m
[32m+[m[32m                await message.answer([m
[32m+[m[32m                    "❌ <b>Ошибка изменения языка</b>\n\n"[m
[32m+[m[32m                    "Попробуйте снова или обратитесь в поддержку.",[m
[32m+[m[32m                    parse_mode="HTML"[m
[32m+[m[32m                )[m
             [m
         else:[m
             await message.answer(f"❌ Неизвестная команда: {action}")[m
[1mdiff --git a/core/i18n/ru.json b/core/i18n/ru.json[m
[1mindex eb78cfd..30fc46d 100644[m
[1m--- a/core/i18n/ru.json[m
[1m+++ b/core/i18n/ru.json[m
[36m@@ -58,6 +58,9 @@[m
   "access_denied": "🚫 Доступ запрещен",[m
   "invalid_data": "❌ Неверные данные",[m
   "try_again": "🔄 Попробуйте снова",[m
[32m+[m[32m  "btn.tariffs": "🏢 Тарифы",[m
[32m+[m[32m  "btn.view_tariffs": "🏢 Посмотреть тарифы",[m
[32m+[m[32m  "help.tariffs": "🏢 **Тарифы KARMABOT1**\n\nВыберите подходящий тариф для вашего бизнеса:\n\n🆓 **FREE STARTER** - 0 VND/мес, 12% комиссия, до 15 транзакций\n💼 **BUSINESS** - 490,000 VND/мес, 6% комиссия, до 100 транзакций\n🏢 **ENTERPRISE** - 960,000 VND/мес, 4% комиссия, безлимит\n\nНажмите кнопку ниже для просмотра детальной информации:",[m
   "profile_main": "👤 **Личный кабинет**",[m
   "profile_stats": "📊 Статистика",[m
   "profile_settings": "⚙️ Настройки",[m
[1mdiff --git a/webapp/admin-cabinet.html b/webapp/admin-cabinet.html[m
[1mindex 064f29c..aa97611 100644[m
[1m--- a/webapp/admin-cabinet.html[m
[1m+++ b/webapp/admin-cabinet.html[m
[36m@@ -266,7 +266,7 @@[m
                 partners: '🏪 Функция "Партнеры" в разработке',[m
                 cards: '🧾 Функция "Карты" в разработке',[m
                 broadcast: '💬 Функция "Рассылка" в разработке',[m
[31m-                'loyalty-settings': '⚙️ Настройки лояльности\n\nОткройте бота и используйте кнопку "⚙️ Настройки лояль�[1mdiff --git a/core/handlers/ai_help.py b/core/handlers/ai_help.py[m
[1mindex 6b1f278..4f88a6c 100644[m
[1m--- a/core/handlers/ai_help.py[m
[1m+++ b/core/handlers/ai_help.py[m
[36m@@ -90,6 +90,12 @@[m [mdef create_help_menu_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:[m
             callback_data="help:contact_support"[m
         )[m
     )[m
[32m+[m[32m    builder.row([m
[32m+[m[32m        InlineKeyboardButton([m
[32m+[m[32m            text=texts.get('btn.tariffs', '🏢 Тарифы'),[m
[32m+[m[32m            callback_data="help:tariffs"[m
[32m+[m[32m        )[m
[32m+[m[32m    )[m
     builder.row([m
         InlineKeyboardButton([m
             text=texts.get('btn.back', '◀️ Назад'),[m
[36m@@ -460,6 +466,53 @@[m [masync def back_to_help_menu(callback: CallbackQuery, state: FSMContext):[m
     except Exception as e:[m
         logger.error(f"Error going back: {e}", exc_info=True)[m
 [m
[32m+[m[32m# Обработчик кнопки "Тарифы"[m
[32m+[m[32m@ai_help_router.callback_query(F.data == "help:tariffs")[m
[32m+[m[32masync def show_tariffs(callback: CallbackQuery, state: FSMContext):[m
[32m+[m[32m    """Показать страницу тарифов"""[m
[32m+[m[32m    try:[m
[32m+[m[32m        user_id = callback.from_user.id[m
[32m+[m[32m        lang = await get_user_lang(user_id)[m
[32m+[m[32m        texts = get_all_texts(lang)[m
[32m+[m[41m        [m
[32m+[m[32m        logger.info(f"[AI_HELP] Tariffs requested by user {user_id}")[m
[32m+[m[41m        [m
[32m+[m[32m        # Создаем WebApp URL для тарифов[m
[32m+[m[32m        from core.services.webapp_integration import create_webapp_url[m
[32m+[m[32m        webapp_url = create_webapp_url(user_id, '/tariffs.html')[m
[32m+[m[41m        [m
[32m+[m[32m        tariff_text = texts.get('help.tariffs',[m
[32m+[m[32m            "🏢 **Тарифы KARMABOT1**\n\n"[m
[32m+[m[32m            "Выберите подходящий тариф для вашего бизнеса:\n\n"[m
[32m+[m[32m            "🆓 **FREE STARTER** - 0 VND/мес, 12% комиссия, до 15 транзакций\n"[m
[32m+[m[32m            "💼 **BUSINESS** - 490,000 VND/мес, 6% комиссия, до 100 транзакций\n"[m
[32m+[m[32m            "🏢 **ENTERPRISE** - 960,000 VND/мес, 4% комиссия, безлимит\n\n"[m
[32m+[m[32m            "Нажмите кнопку ниже для просмотра детальной информации:"[m
[32m+[m[32m        )[m
[32m+[m[41m        [m
[32m+[m[32m        keyboard = InlineKeyboardMarkup(inline_keyboard=[[m
[32m+[m[32m            [InlineKeyboardButton([m
[32m+[m[32m                text=texts.get('btn.view_tariffs', '🏢 Посмотреть тарифы'),[m
[32m+[m[32m                web_app=WebAppInfo(url=webapp_url)[m
[32m+[m[32m            )],[m
[32m+[m[32m            [InlineKeyboardButton([m
[32m+[m[32m                text=texts.get('btn.back', '◀️ Назад'),[m
[32m+[m[32m                callback_data="help:back"[m
[32m+[m[32m            )][m
[32m+[m[32m        ])[m
[32m+[m[41m        [m
[32m+[m[32m        await callback.message.edit_text([m
[32m+[m[32m            tariff_text,[m
[32m+[m[32m            reply_markup=keyboard,[m
[32m+[m[32m            parse_mode="HTML"[m
[32m+[m[32m        )[m
[32m+[m[41m        [m
[32m+[m[32m        await callback.answer()[m
[32m+[m[41m        [m
[32m+[m[32m    except Exception as e:[m
[32m+[m[32m        logger.error(f"Error showing tariffs: {e}", exc_info=True)[m
[32m+[m[32m        await callback.answer("❌ Ошибка при загрузке тарифов", show_alert=True)[m
[32m+[m
 # Обработчик возврата в главное меню[m
 @ai_help_router.callback_query(F.data == "help:main_menu")[m
 async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):[m
[1mdiff --git a/core/handlers/webapp_handler.py b/core/handlers/webapp_handler.py[m
[1mindex a45cb66..8769e08 100644[m
[1m--- a/core/handlers/webapp_handler.py[m
[1m+++ b/core/handlers/webapp_handler.py[m
[36m@@ -64,6 +64,29 @@[m [masync def handle_webapp_data(message: Message):[m
                 f"• Сохранение данных в браузере",[m
                 parse_mode="HTML"[m
             )[m
[32m+[m[41m        [m
[32m+[m[32m        elif action == 'change_language':[m
[32m+[m[32m            # Изменение языка пользователя[m
[32m+[m[32m            language = data.get('language', 'ru')[m
[32m+[m[32m            logger.info(f"[WEBAPP] Language change request from user {user_id}: {language}")[m
[32m+[m[41m            [m
[32m+[m[32m            # Обновляем язык пользователя в БД[m
[32m+[m[32m            from core.services.translation_service import translation_service[m
[32m+[m[32m            success = translation_service.set_user_language(user_id, language)[m
[32m+[m[41m            [m
[32m+[m[32m            if success:[m
[32m+[m[32m                await message.answer([m
[32m+[m[32m                    f"✅ <b>Язык изменен!</b>\n\n"[m
[32m+[m[32m                    f"Интерфейс переключен на: {translation_service.get_language_name(language)}\n\n"[m
[32m+[m[32m                    f"Изменения вступят в силу при следующем открытии кабинета.",[m
[32m+[m[32m                    parse_mode="HTML"[m
[32m+[m[32m                )[m
[32m+[m[32m            else:[m
[32m+[m[32m                await message.answer([m
[32m+[m[32m                    "❌ <b>Ошибка изменения языка</b>\n\n"[m
[32m+[m[32m                    "Попробуйте снова или обратитесь в поддержку.",[m
[32m+[m[32m                    parse_mode="HTML"[m
[32m+[m[32m                )[m
             [m
         else:[m
             await message.answer(f"❌ Неизвестная команда: {action}")[m
[1mdiff --git a/core/i18n/ru.json b/core/i18n/ru.json[m
[1mindex eb78cfd..30fc46d 100644[m
[1m--- a/core/i18n/ru.json[m
[1m+++ b/core/i18n/ru.json[m
[36m@@ -58,6 +58,9 @@[m
   "access_denied": "🚫 Доступ запрещен",[m
   "invalid_data": "❌ Неверные данные",[m
   "try_again": "🔄 Попробуйте снова",[m
[32m+[m[32m  "btn.tariffs": "🏢 Тарифы",[m
[32m+[m[32m  "btn.view_tariffs": "🏢 Посмотреть тарифы",[m
[32m+[m[32m  "help.tariffs": "🏢 **Тарифы KARMABOT1**\n\nВыберите подходящий тариф для вашего бизнеса:\n\n🆓 **FREE STARTER** - 0 VND/мес, 12% комиссия, до 15 транзакций\n💼 **BUSINESS** - 490,000 VND/мес, 6% комиссия, до 100 транзакций\n🏢 **ENTERPRISE** - 960,000 VND/мес, 4% комиссия, безлимит\n\nНажмите кнопку ниже для просмотра детальной информации:",[m
   "profile_main": "👤 **Личный кабинет**",[m
   "profile_stats": "📊 Статистика",[m
   "profile_settings": "⚙️ Настройки",[m
[1mdiff --git a/webapp/admin-cabinet.html b/webapp/admin-cabinet.html[m
[1mindex 064f29c..aa97611 100644[m
[1m--- a/webapp/admin-cabinet.html[m
[1m+++ b/webapp/admin-cabinet.html[m
[36m@@ -266,7 +266,7 @@[m
                 partners: '🏪 Функция "Партнеры" в разработке',[m
                 cards: '🧾 Функция "Карты" в разработке',[m
                 broadcast: '💬 Функция "Рассылка" в разработке',[m
[31m-                'loyalty-settings': '⚙️ Настройки лояльности\n\nОткройте бота и используйте кнопку "⚙️ Настройки лояль�