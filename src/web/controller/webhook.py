from logging import Logger
from flask import Response, request, url_for
from mongoengine import DoesNotExist
import hmac
from urllib.parse import urlparse
from datetime import datetime, timezone

from src.toggl.model import TagData
from src.db.entity import User, Tag


class Webhook:
    def __init__(self, logger: Logger) -> None:
        self.logger = logger

    def process(self, workspace_id: int, user_id: int) -> Response | str:
        # Check if user could be found
        try:
            user = User.objects.get(user_id=user_id)
        except DoesNotExist:
            return "not found", 404

        # Check if user workspace could be found
        user_workspace = None
        for u_workspace in user.workspaces:
            if u_workspace.workspace.workspace_id == workspace_id:
                user_workspace = u_workspace
                break
        if user_workspace is None:
            return "not found", 404

        # Validate content type
        if not request.is_json:
            return "invalid content type", 406

        # Validate hmac signature
        secret = user_workspace.subscription_token
        message = request.data
        signature = request.headers["x-webhook-signature-256"]
        digest = hmac.new(secret.encode("utf-8"), message, "sha256").hexdigest()
        if not hmac.compare_digest(signature, f"sha256={digest}"):
            return "invalid signature", 401

        # Validate url_callback
        request_url = urlparse(request.json["url_callback"])
        generated_url = urlparse(
            url_for(
                "webhook",
                _external=True,
                workspace_id=workspace_id,
                user_id=user.user_id,
            )
        )
        if (
            request_url.netloc != generated_url.netloc
            or request_url.path != generated_url.path
        ):
            return "invalid callback url", 400

        # Answer validation requests from toggl
        event = request.json
        response = {}
        if "validation_code" in event:
            response["validation_code"] = event["validation_code"]

        # Ignore events of other users, when an admin has created the webhook
        if event["creator_id"] != user_id:
            self.webhook_logger.info("Ignore event for other user")
        else:
            # Set info about webhook events
            user_workspace.last_webhook_event_received_at = datetime.now(timezone.utc)
            user.save()

            # Process webhook payload
            if event["payload"] == "ping":
                self.logger.info(
                    "%s ping",
                    event["metadata"]["event_user_id"],
                )
            else:
                self.logger.info(
                    "%s %s %s %s",
                    event["metadata"]["event_user_id"],
                    event["metadata"]["action"],
                    event["metadata"]["model"],
                    event["metadata"]["path"],
                )

                match event["metadata"]["model"]:
                    case "tag":
                        tag_data = TagData.from_dict(event["payload"])
                        if event["metadata"]["action"] in ("created", "updated"):
                            Tag.create_or_update_tag_from_api(tag_data)
                        elif event["metadata"]["action"] == "deleted":
                            # toggl api does not send this event :(
                            pass

        return response, 200
