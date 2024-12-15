from functools import wraps
from flask import g, request, redirect, url_for, session, render_template, flash


def login_required(f):
    """
    Decorator that ensures a user is logged in before accessing a route.

    This decorator checks if the user is logged in by verifying the presence of a "user" key in the session.
    If the user is not logged in, it redirects them to the login page and passes the original URL as a "next" parameter.

    Args:
        f (function): The route function to be decorated.

    Returns:
        function: The decorated function that includes the login check.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user") is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def check_and_flash_if_none(check, return_path, message):
    if check is None:
        flash(message, "error")
        return render_template(return_path, error=message)
    