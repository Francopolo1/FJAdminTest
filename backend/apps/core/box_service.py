"""
Box.com integration — Client Credentials Grant (service account) helper.

Authenticates server-to-server as a Box "Custom App" service account, with
no per-user OAuth/consent flow.  Used to create (or reuse) a documents
folder for a checklist response and return its shareable URL.
"""

from functools import lru_cache

from django.conf import settings
from boxsdk import Client, CCGAuth
from boxsdk.exception import BoxAPIException

__all__ = ["BoxConfigError", "BoxAPIException", "get_or_create_folder"]


class BoxConfigError(Exception):
    """Raised when Box service-account credentials are not configured."""


@lru_cache(maxsize=1)
def _get_client():
    if not (settings.BOX_CLIENT_ID and settings.BOX_CLIENT_SECRET and settings.BOX_ENTERPRISE_ID):
        raise BoxConfigError(
            "Box is not configured. Set BOX_CLIENT_ID, BOX_CLIENT_SECRET and "
            "BOX_ENTERPRISE_ID (from a Box Custom App with Client Credentials "
            "Grant enabled) in the environment."
        )

    auth = CCGAuth(
        client_id=settings.BOX_CLIENT_ID,
        client_secret=settings.BOX_CLIENT_SECRET,
        enterprise_id=settings.BOX_ENTERPRISE_ID,
    )
    return Client(auth)


def get_or_create_folder(name, parent_id=None):
    """
    Return (folder_id, folder_url) for a folder named `name` under
    `parent_id` (defaults to BOX_PARENT_FOLDER_ID, or "0" for the root).

    If a folder with that name already exists directly under the parent,
    it is reused instead of creating a duplicate.
    """
    client    = _get_client()
    parent_id = parent_id or settings.BOX_PARENT_FOLDER_ID or "0"
    parent    = client.folder(folder_id=parent_id)

    for item in parent.get_items():
        if item.type == "folder" and item.name == name:
            return item.id, f"https://app.box.com/folder/{item.id}"

    folder = parent.create_subfolder(name)
    return folder.id, f"https://app.box.com/folder/{folder.id}"
