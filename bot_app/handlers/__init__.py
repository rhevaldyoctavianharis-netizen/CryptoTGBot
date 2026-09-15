from . import start, commands, user_menu, admin_menu, text_input, poller


def register_all(client):
    start.register(client)
    commands.register(client)
    user_menu.register(client)
    # admin_menu di-handle dari user_menu callback (bukan register terpisah)
    text_input.register(client)
    poller.start_poller()