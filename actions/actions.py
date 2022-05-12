from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction, Form
import json
from actions.search_engine_api_wrapper import get_report, get_search_results, get_questions, get_sector_description, get_bc_attribute_list
import difflib


QUESTIONS = get_questions()
FEATURES = [q["feature"] for q in QUESTIONS]


class ActionAskQuestion(Action):

    def name(self) -> Text:
        return "action_ask_question"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        load_questions()
        for q in QUESTIONS:
            if not tracker.slots[q["feature"]]:
                question = q
                break
        if question["type"] == "open":
            dispatcher.utter_message(text=question["question"])
        else:
            if question["adapt_on_sector"]:
                data = [{"label": r, "value": r}
                        for r in get_bc_attribute_list(q["feature"], filter={"attribute": "sector", "value": tracker.slots["sector"]})]
            else:
                data = [{"label": r, "value": r}
                        for r in question["responses"]]
            if question["allow_unknown"]:
                data.append({"label": "I don't know", "value": "Unknown"})
            if question["type"] == "multiple_choice":
                message = {"payload": "multiDropDown", "data": data}
            elif question["type"] == "single_choice":
                message = {"payload": "dropDown", "data": data}
            dispatcher.utter_message(
                text=question["question"], json_message=message)
        return [SlotSet(key="active_feature", value=question["feature"])]


class ActionParseResponse(Action):

    def name(self) -> Text:
        return "action_parse_response"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        response = tracker.latest_message["text"]
        feature = tracker.slots["active_feature"]
        tracker.slots[feature] = response
        message = {"payload": "visualization_content",
                   "data": json.dumps(get_visualization_content(tracker))}
        dispatcher.utter_message(json_message=message)
        if all([tracker.slots[q["feature"]] for q in QUESTIONS]):
            return [SlotSet(key=feature, value=response), SlotSet("active_feature", value=None), FollowupAction(name="action_present_results")]
        return [SlotSet(key=feature, value=response), SlotSet("active_feature", value=None), FollowupAction(name="action_ask_question")]


class ActionFlushSearchState(Action):

    def name(self):
        return "action_flush_search_state"

    def run(self, dispatcher, tracker, domain):
        load_questions()
        dispatcher.utter_message(text="The search space has been reset")
        return [SlotSet(key=slot, value=None) for slot in FEATURES]


class ActionRectify(Action):
    def name(self):
        return "action_rectify"

    def run(self, dispatcher, tracker, domain):
        try:
            feature = tracker.latest_message["entities"][0]["value"]
            feature = search_feature(feature, FEATURES)
            return [SlotSet(key=feature, value=None), FollowupAction(name="action_ask_question")]
        except IndexError:
            dispatcher.utter_message(
                text="I did not understand the feature you want to correct, could you please reformulate ?")


class ActionPresentResults(Action):
    def name(self):
        return "action_present_results"

    def run(self, dispatcher, tracker, domain):
        top_business_cases = get_current_results(tracker)[0:3]
        url = get_report(tracker.slots, top_business_cases)
        data = {"payload": "pdf_attachment",
                "title": "Reports", "url": url}
        dispatcher.utter_message(json_message=data)
        dispatcher.utter_message(
            text="Here is the generated report")
        return [FollowupAction(name="utter_ask_send_email")]


class ActionBack(Action):
    def name(self):
        return "action_go_back"

    def run(self, dispatcher, tracker, domain):
        for e in tracker.events:
            print(e['event'])
        print(tracker.events[-6])
        return []


class ActionSendResults(Action):
    def name(self):
        return "action_send_results"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(
            text=f"The report was sent at {tracker.slots['email']}")
        return [FollowupAction(name="utter_restart")]


def get_current_results(tracker):
    open_knowledge = {q["feature"]: tracker.slots[q["feature"]]
                      for q in QUESTIONS if tracker.slots[q["feature"]] is not None and q["type"] == "open"}

    feature_knowledge = {q["feature"]: tracker.slots[q["feature"]]
                         for q in QUESTIONS if tracker.slots[q["feature"]] is not None and tracker.slots[q["feature"]] != "Unknown" and q["type"] in ["multiple_choice", "single_choice"]}
    query = " ".join(list(open_knowledge.values())) + " " +\
        " ".join(list(feature_knowledge.values()))
    return get_search_results(feature_knowledge, query=query)


def get_visualization_content(tracker):
    results = {}
    if tracker.slots["active_feature"] == "sector":
        sector_description = get_sector_description(
            tracker.slots["sector"])
        results["sector_description"] = {
            "sector": tracker.slots["sector"], "description": sector_description}
    results["business_cases"] = get_current_results(tracker)
    return results


def search_feature(feature_name, feature_list):
    return difflib.get_close_matches(feature_name, feature_list, n=1)[0]


def load_questions():
    global QUESTIONS
    global FEATURES
    if not QUESTIONS:
        QUESTIONS = get_questions()
        FEATURES = [q["feature"] for q in QUESTIONS]
