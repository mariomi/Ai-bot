import os, msal, requests
from typing import Dict, Any, List

TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}" if TENANT_ID else None
SCOPE = ["https://graph.microsoft.com/.default"]

def get_graph_token() -> str:
    if not (TENANT_ID and CLIENT_ID and CLIENT_SECRET):
        raise RuntimeError("Graph env vars missing")
    app = msal.ConfidentialClientApplication(
        client_id=CLIENT_ID, client_credential=CLIENT_SECRET, authority=AUTHORITY
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    if "access_token" not in result:
        raise RuntimeError(result.get("error_description"))
    return result["access_token"]

def graph_get(url: str, token: str, params=None) -> Dict[str, Any]:
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params)
    r.raise_for_status()
    return r.json()

def list_messages(user_id: str, top: int = 20) -> List[Dict[str, Any]]:
    token = get_graph_token()
    url = f"https://graph.microsoft.com/v1.0/users/{user_id}/messages"
    params = {
        "$top": top,
        "$orderby": "receivedDateTime desc",
        "$select": "id,conversationId,sentDateTime,receivedDateTime,subject,from,toRecipients,ccRecipients,hasAttachments,bodyPreview,importance,internetMessageHeaders"
    }
    data = graph_get(url, token, params)
    return data.get("value", [])

def get_message(user_id: str, message_id: str) -> Dict[str, Any]:
    token = get_graph_token()
    url = f"https://graph.microsoft.com/v1.0/users/{user_id}/messages/{message_id}"
    params = {"$select": "id,conversationId,subject,from,toRecipients,ccRecipients,bccRecipients,sentDateTime,receivedDateTime,body,hasAttachments,importance,internetMessageHeaders"}
    return graph_get(url, token, params)
