import os


def get_setting():
    env = os.getenv("ENV", "development")

    if env == 'development':
        from .development import Setting

    elif env == 'staging':
        from .staging import Setting

    else:
        raise ValueError(f'Unknown environment {env}')

    return Setting
