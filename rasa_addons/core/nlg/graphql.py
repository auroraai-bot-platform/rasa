import logging
from typing import Text, Any, Dict, Optional, List
from rasa_addons.core.nlg.nlg_helper import rewrite_url
from rasa.core.constants import DEFAULT_REQUEST_TIMEOUT
from rasa.core.nlg.generator import NaturalLanguageGenerator
from rasa.shared.core.trackers import DialogueStateTracker, EventVerbosity
from rasa.utils.endpoints import EndpointConfig
import os
import urllib.error
from rasa.core.nlg.interpolator import interpolate

logger = logging.getLogger(__name__)


NLG_QUERY = """
fragment CarouselElementFields on CarouselElement {
    title
    subtitle
    image_url
    default_action { title, type, ...on WebUrlButton { url }, ...on PostbackButton { payload } }
    buttons { title, type, ...on WebUrlButton { url }, ...on PostbackButton { payload } }
}
query(
    $template: String!
    $arguments: Any
    $tracker: ConversationInput
    $channel: NlgRequestChannel
) {
    getResponse(
        template: $template
        arguments: $arguments
        tracker: $tracker
        channel: $channel
    ) {
        metadata
        ...on TextPayload { text }
        ...on QuickRepliesPayload { text, quick_replies { title, type, ...on WebUrlButton { url }, ...on PostbackButton { payload } } }
        ...on TextWithButtonsPayload { text, buttons { title, type, ...on WebUrlButton { url }, ...on PostbackButton { payload } } }
        ...on ImagePayload { text, image }
        ...on VideoPayload { text, custom }
        ...on CarouselPayload { template_type, elements { ...CarouselElementFields } }
        ...on CustomPayload { customText: text, customImage: image, customQuickReplies: quick_replies, customButtons: buttons, customElements: elements, custom, customAttachment: attachment }
    }
}
"""


def nlg_response_format_spec():
    """Expected response schema for an NLG endpoint.

    Used for validation of the response returned from the NLG endpoint."""
    return {
        "type": "object",
        "properties": {
            "text": {"type": ["string", "null"]},
            "buttons": {"type": ["array", "null"], "items": {"type": "object"}},
            "elements": {"type": ["array", "null"], "items": {"type": "object"}},
            "attachment": {"type": ["object", "null"]},
            "image": {"type": ["string", "null"]},
        },
    }


def nlg_request_format_spec():
    """Expected request schema for requests sent to an NLG endpoint."""

    return {
        "type": "object",
        "properties": {
            "template": {"type": "string"},
            "arguments": {"type": "object"},
            "tracker": {
                "type": "object",
                "properties": {
                    "sender_id": {"type": "string"},
                    "slots": {"type": "object"},
                    "latest_message": {"type": "object"},
                    "latest_event_time": {"type": "number"},
                    "paused": {"type": "boolean"},
                    "events": {"type": "array"},
                },
            },
            "channel": {"type": "object", "properties": {"name": {"type": "string"}}},
        },
    }


def nlg_request_format(
    template_name: Text,
    tracker: DialogueStateTracker,
    output_channel: Text,
    **kwargs: Any,
) -> Dict[Text, Any]:
    """Create the json body for the NLG json body for the request."""

    tracker_state = tracker.current_state(EventVerbosity.ALL)

    return {
        "template": template_name,
        "arguments": kwargs,
        "tracker": tracker_state,
        "channel": {"name": output_channel},
    }


class GraphQLNaturalLanguageGenerator(NaturalLanguageGenerator):
    """Like Rasa's CallbackNLG, but queries Botfront's GraphQL endpoint"""

    def __init__(self, **kwargs) -> None:
        self.nlg_endpoint = kwargs.get("endpoint_config")
        self.url_substitution_patterns = []
        if self.nlg_endpoint:
            self.url_substitution_patterns = (
                self.nlg_endpoint.kwargs.get("url_substitutions") or []
            )

    async def generate(
        self,
        template_name: Text,
        tracker: DialogueStateTracker,
        output_channel: Text,
        **kwargs: Any,
    ) -> List[Dict[Text, Any]]:

        fallback_language_slot = tracker.slots.get("fallback_language")
        fallback_language = (
            fallback_language_slot.initial_value if fallback_language_slot else None
        )
        language = tracker.latest_message.metadata.get("language") or fallback_language

        body = nlg_request_format(
            template_name,
            tracker,
            output_channel,
            **kwargs,
            language=language,
            projectId=os.environ.get("BF_PROJECT_ID"),
            environment=os.environ.get("BOTFRONT_ENV", "development"),
        )

        logger.debug(
            "Requesting NLG for {} from {}."
            "".format(template_name, self.nlg_endpoint.url)
        )

        try:
            if "graphql" in self.nlg_endpoint.url:
                from sgqlc.endpoint.http import HTTPEndpoint

                logging.getLogger("sgqlc.endpoint.http").setLevel(logging.WARNING)

                api_key = os.environ.get("API_KEY")
                headers = [{"Authorization": api_key}] if api_key else []
                response = HTTPEndpoint(self.nlg_endpoint.url, *headers)(
                    NLG_QUERY, body
                )
                if response.get("errors"):
                    raise urllib.error.URLError(
                        ", ".join([e.get("message") for e in response.get("errors")])
                    )
                response = response.get("data", {}).get("getResponse", {})
                rewrite_url(response, self.url_substitution_patterns)
                if "customText" in response:
                    response["text"] = response.pop("customText")
                if "customImage" in response:
                    response["image"] = response.pop("customImage")
                if "customQuickReplies" in response:
                    response["quick_replies"] = response.pop("customQuickReplies")
                if "customButtons" in response:
                    response["buttons"] = response.pop("customButtons")
                if "customElements" in response:
                    response["elements"] = response.pop("customElements")
                if "customAttachment" in response:
                    response["attachment"] = response.pop("customAttachment")
                metadata = response.pop("metadata", {}) or {}
                for key in metadata:
                    response[key] = metadata[key]
                response["template_name"] = template_name

                keys_to_interpolate = [
                    "text",
                    "image",
                    "custom",
                    "buttons",
                    "attachment",
                    "quick_replies",
                ]
                for key in keys_to_interpolate:
                    if key in response:
                        response[key] = interpolate(response[key], tracker.current_slot_values())
            else:
                response = await self.nlg_endpoint.request(
                    method="post", json=body, timeout=DEFAULT_REQUEST_TIMEOUT
                )
                response = response[0]  # legacy route, use first message in seq
        except urllib.error.URLError as e:
            message = e.reason
            logger.error(
                f"NLG web endpoint at {self.nlg_endpoint.url} returned errors: {message}"
            )
            return {"text": template_name}

        if self.validate_response(response):
            return response
        else:
            logger.error(
                f"NLG web endpoint at {self.nlg_endpoint.url} returned an invalid response."
            )
            return {"text": template_name}

    @staticmethod
    def validate_response(content: Optional[Dict[Text, Any]]) -> bool:
        """Validate the NLG response. Raises exception on failure."""

        from jsonschema import validate
        from jsonschema import ValidationError

        try:
            if content is None or content == "":
                # means the endpoint did not want to respond with anything
                return True
            else:
                validate(content, nlg_response_format_spec())
                return True
        except ValidationError as e:
            e.message += (
                ". Failed to validate NLG response from API, make sure your "
                "response from the NLG endpoint is valid. "
                "For more information about the format please consult the "
                "`nlg_response_format_spec` function from this same module: "
                "https://github.com/RasaHQ/rasa/blob/master/rasa/core/nlg/callback.py#L12"
            )
            raise e
