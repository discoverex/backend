from src.configs.setting import MAGIC_EYE_PORT, GAME_HUB_PORT, DISCOVEREX_PORT,  APP_PORT, GAME_HUB_URL, DISCOVEREX_URL, MAGIC_EYE_URL

origins = [
    f"http://localhost:{APP_PORT}",
    f"http://127.0.0.1:{APP_PORT}",
    f"http://localhost:{GAME_HUB_PORT}",
    f"http://127.0.0.1:{GAME_HUB_PORT}",
    f"http://localhost:{DISCOVEREX_PORT}",
    f"http://127.0.0.1:{DISCOVEREX_PORT}",
    f"http://localhost:{MAGIC_EYE_PORT}",
    f"http://127.0.0.1:{MAGIC_EYE_PORT}",
    f"{GAME_HUB_URL}"
    f"{DISCOVEREX_URL}"
    f"{MAGIC_EYE_URL}"
]
