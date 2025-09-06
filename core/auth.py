def authenticate_user(token):
    return {"user_id": 1, "username": "admin"}

def require_auth(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def get_current_user():
    return {"id": 1, "role": "admin"}
