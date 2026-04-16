from PROJECT.channels.telegram.app import create_application
from PROJECT.settings import load_settings


def main() -> None:
    settings = load_settings()
    application = create_application(settings)
    application.run_polling()


if __name__ == "__main__":
    main()
