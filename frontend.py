"""Streamlit frontend for the FastAPI photo and video feed."""

import os
from datetime import datetime
from typing import Any, cast

import requests
import streamlit as st

API_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT = 30

st.set_page_config(page_title="Open Frame", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    :root {
        --ink: #172a25;
        --muted: #65766f;
        --forest: #174b3d;
        --lime: #c9ec76;
        --coral: #e66b52;
    }
    .stApp {
        background: linear-gradient(135deg, #f3f7f2 0%, #e9f0ec 58%, #f7f3ed 100%);
        color: var(--ink);
        font-family: 'DM Sans', sans-serif;
    }
    [data-testid='stHeader'] {
        background: transparent;
    }
    [data-testid='stMain'] {
        background: transparent;
    }
    h1, h2, h3, [data-testid='stMetricValue'] {
        font-family: 'Manrope', sans-serif;
        color: var(--ink);
    }
    .stApp h1 {
        line-height: 1.2;
        margin: 0;
        padding-top: 0.15rem;
        padding-bottom: 0.4rem;
    }
    .block-container {
        max-width: 1120px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }
    .st-key-auth-panel {
        max-width: 720px;
        margin: 2rem auto 0;
    }
    section[data-testid='stSidebar'] {
        background: #15372f;
        border-right: 1px solid #285448;
    }
    section[data-testid='stSidebar'] * {
        color: #eaf2ed;
    }
    section[data-testid='stSidebar'] [data-testid='stMarkdownContainer'] p {
        color: #b9cdc2;
    }
    [data-testid='stVerticalBlockBorderWrapper'] {
        background: rgba(255, 255, 255, 0.82);
        border-color: rgba(23, 42, 37, 0.11);
        border-radius: 8px;
    }
    .wordmark {
        font-family: 'Manrope', sans-serif;
        color: #f4f8f4;
        font-size: 1.08rem;
        font-weight: 800;
        letter-spacing: 0.02em;
        padding: 0.65rem 0 1.75rem;
    }
    .eyebrow {
        color: var(--forest);
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.5rem;
    }
    .stButton > button, .stFormSubmitButton > button {
        border-radius: 6px;
        font-weight: 600;
        min-height: 2.65rem;
    }
    .stButton > button[kind='primary'], .stFormSubmitButton > button[kind='primary'] {
        background: var(--forest);
        border-color: var(--forest);
        color: white;
    }
    .stButton > button[kind='primary']:hover,
    .stFormSubmitButton > button[kind='primary']:hover {
        background: #23664f;
        border-color: #23664f;
        color: white;
    }
    div[data-baseweb='input'] input, div[data-baseweb='textarea'] textarea {
        border-radius: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    **kwargs: Any,
) -> requests.Response | None:
    """Send an API request and report connection failures in the UI."""
    headers = dict(kwargs.pop("headers", {}))
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        return requests.request(
            method,
            f"{API_BASE_URL}{path}",
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )
    except requests.RequestException as error:
        st.error(f"Could not reach the API at {API_BASE_URL}: {error}")
        return None


def response_detail(response: requests.Response) -> str:
    """Return the API error detail or a status-based fallback."""
    try:
        payload = cast(dict[str, Any], response.json())
    except ValueError:
        return f"Request failed with HTTP {response.status_code}."

    return str(payload.get("detail", payload))


def clear_authentication() -> None:
    """Remove the current user's token and email from Streamlit state."""
    st.session_state.pop("access_token", None)
    st.session_state.pop("user_email", None)


def authenticate(email: str, password: str) -> bool:
    """Log in with email and password and store the returned access token."""
    response = api_request(
        "POST",
        "/auth/jwt/login",
        data={"username": email, "password": password},
    )
    if response is None:
        return False
    if response.status_code != 200:
        st.error(response_detail(response))
        return False

    payload = response.json()
    st.session_state.access_token = payload["access_token"]
    st.session_state.user_email = email
    st.session_state.page = "Feed"
    return True


def render_authentication() -> None:
    """Render the sign-in and account registration forms."""
    with st.container(border=True, key="auth-panel"):
        st.markdown('<div class="eyebrow">OPEN FRAME</div>', unsafe_allow_html=True)
        st.title("Welcome back.")
        st.caption("Sign in or create an account to continue.")
        sign_in, register = st.tabs(["Sign in", "Create account"])

        with sign_in:
            with st.form("sign_in_form"):
                email = st.text_input("Email", autocomplete="email")
                password = st.text_input(
                    "Password", type="password", autocomplete="current-password"
                )
                submitted = st.form_submit_button(
                    "Sign in", type="primary", use_container_width=True
                )
            if submitted and email and password and authenticate(email, password):
                st.rerun()
            elif submitted and (not email or not password):
                st.error("Enter your email and password.")

        with register:
            with st.form("register_form"):
                new_email = st.text_input("Email", key="register_email")
                new_password = st.text_input(
                    "Password",
                    type="password",
                    autocomplete="new-password",
                    key="register_password",
                )
                submitted = st.form_submit_button(
                    "Create account", type="primary", use_container_width=True
                )
            if submitted:
                if not new_email or not new_password:
                    st.error("Enter an email and password.")
                else:
                    response = api_request(
                        "POST",
                        "/auth/register",
                        json={"email": new_email, "password": new_password},
                    )
                    if response is not None:
                        if response.status_code == 201:
                            if authenticate(new_email, new_password):
                                st.rerun()
                            st.success("Account created. You can now sign in.")
                        else:
                            st.error(response_detail(response))


def expire_session() -> None:
    """Clear expired credentials and return the user to sign-in."""
    clear_authentication()
    st.warning("Your session expired. Sign in again.")
    st.rerun()


def format_created_at(value: str) -> str:
    """Format an ISO timestamp for display in a post."""
    try:
        created_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return created_at.astimezone().strftime("%b %d, %Y at %I:%M %p")
    except ValueError, TypeError:
        return value


def render_feed() -> None:
    """Fetch and render feed posts with owner-only delete actions."""
    header, refresh = st.columns([5, 1], vertical_alignment="center")
    with header:
        st.markdown('<div class="eyebrow">YOUR COMMUNITY</div>', unsafe_allow_html=True)
        st.title("The feed")
    with refresh:
        if st.button("Refresh", icon=":material/refresh:", use_container_width=True):
            st.rerun()

    response = api_request("GET", "/feed", token=st.session_state.access_token)
    if response is None:
        return
    if response.status_code == 401:
        expire_session()
    if not response.ok:
        st.error(response_detail(response))
        return

    posts = response.json().get("posts", [])
    st.caption(f"{len(posts)} posts")
    if not posts:
        with st.container(border=True):
            st.subheader("Nothing here yet")
            st.caption("Your community feed is quiet for now.")
        return

    for post in posts:
        with st.container(border=True):
            author, action = st.columns([5, 1], vertical_alignment="center")
            with author:
                st.write(post.get("email", "Unknown member"))
                st.caption(format_created_at(post.get("created_at", "")))
            with action:
                if post.get("is_owner") and st.button(
                    "Delete",
                    key=f"delete_{post['id']}",
                    icon=":material/delete_outline:",
                    type="secondary",
                    use_container_width=True,
                ):
                    delete_response = api_request(
                        "DELETE",
                        f"/posts/{post['id']}",
                        token=st.session_state.access_token,
                    )
                    if delete_response is None:
                        return
                    if delete_response.status_code == 401:
                        expire_session()
                    if delete_response.ok:
                        st.toast("Post deleted")
                        st.rerun()
                    st.error(response_detail(delete_response))

            if post.get("file_type") == "video":
                st.video(post["url"])
            else:
                st.image(post["url"], use_container_width=True)
            caption = post.get("caption")
            if caption:
                st.write(caption)
            st.caption(post.get("file_name", ""))


def render_composer() -> None:
    """Render the media upload and caption form for a new post."""
    st.markdown('<div class="eyebrow">NEW POST</div>', unsafe_allow_html=True)
    st.title("Share a moment")

    with st.container(border=True):
        with st.form("create_post_form", clear_on_submit=True):
            uploaded_file = st.file_uploader(
                "Photo or video",
                type=["jpg", "jpeg", "png", "webp", "gif", "mp4", "mov", "webm"],
            )
            caption = st.text_area("Caption", max_chars=2000, height=110)
            submitted = st.form_submit_button(
                "Publish post", type="primary", icon=":material/arrow_upward:"
            )

        if submitted:
            if uploaded_file is None:
                st.error("Choose a photo or video first.")
                return
            response = api_request(
                "POST",
                "/upload",
                token=st.session_state.access_token,
                data={"caption": caption},
                files={
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type or "application/octet-stream",
                    )
                },
            )
            if response is None:
                return
            if response.status_code == 401:
                expire_session()
            if response.ok:
                st.session_state.page = "Feed"
                st.toast("Post published")
                st.rerun()
            st.error(response_detail(response))


def render_dashboard() -> None:
    """Render the authenticated navigation and selected page."""
    if "page" not in st.session_state:
        st.session_state.page = "Feed"

    with st.sidebar:
        st.markdown('<div class="wordmark">OPEN FRAME</div>', unsafe_allow_html=True)
        st.caption("SIGNED IN AS")
        st.write(st.session_state.get("user_email", ""))
        st.divider()
        current_page = st.session_state.page
        st.button(
            "Feed",
            icon=":material/view_stream:",
            type="primary" if current_page == "Feed" else "secondary",
            use_container_width=True,
            on_click=lambda: st.session_state.update(page="Feed"),
        )
        st.button(
            "Create post",
            icon=":material/add_photo_alternate:",
            type="primary" if current_page == "Create post" else "secondary",
            use_container_width=True,
            on_click=lambda: st.session_state.update(page="Create post"),
        )
        st.divider()
        if st.button(
            "Sign out",
            icon=":material/logout:",
            use_container_width=True,
        ):
            api_request("POST", "/auth/jwt/logout", token=st.session_state.access_token)
            clear_authentication()
            st.rerun()

    if st.session_state.page == "Create post":
        render_composer()
    else:
        render_feed()


if "access_token" in st.session_state:
    render_dashboard()
else:
    render_authentication()
