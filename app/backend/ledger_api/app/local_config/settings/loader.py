import os


def load_settings():
    """環境に応じた設定をロードして返す"""
    app_env = os.getenv("APP_ENV", "dev")

    if app_env == "prod":
        from app.local_config.settings import prod as settings_module
    elif app_env == "staging":
        from app.local_config.settings import staging as settings_module
    else:
        from app.local_config.settings import dev as settings_module

    settings = {
        "ENV_NAME": settings_module.ENV_NAME,
        "DEBUG": settings_module.DEBUG,
        "STREAMLIT_SERVER_PORT": settings_module.STREAMLIT_SERVER_PORT,
    }
    return settings
