from src.configs.setting import WEB_PORT, APP_PORT, GAME_HUB_URL, DISCOVEREX_URL, MAGIC_EYE_URL

origins = [
    f"http://localhost:{WEB_PORT}",
    f"http://127.0.0.1:{WEB_PORT}",
    f"http://localhost:{APP_PORT}",
    f"http://127.0.0.1:{APP_PORT}",
    f"{GAME_HUB_URL}"
    f"{DISCOVEREX_URL}"
    f"{MAGIC_EYE_URL}"
    # f"http://{REMOTE_HOST}:{APP_PORT}",
    # f"http://{REMOTE_HOST}:{WEB_PORT}",
    # f"http://{REMOTE_HOST}",
]
