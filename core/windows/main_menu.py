main_menu_text = "main_menu"

# совместимость: гарантируем наличие get_main_menu
if "get_main_menu" not in globals():
    if "build_main_menu" in globals():
        get_main_menu = build_main_menu  # type: ignore
    elif "get_main_menu_kb" in globals():
        get_main_menu = get_main_menu_kb  # type: ignore
    elif "main_menu" in globals() and callable(main_menu):
        get_main_menu = main_menu  # type: ignore
