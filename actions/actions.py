from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
import pandas as pd
import actions.search_engine_api_wrapper
import json

FEATURE_QUESTIONS = pd.read_csv("data/questions/feature_questions.csv")
OPEN_QUESTIONS = pd.read_csv("data/questions/open_questions.csv")
with open("data/sector_presentation.json", "r") as f:
    SECTOR_PRESENTATION = json.load(f)


class ActionAskFeatureQuestion(Action):

    def name(self) -> Text:
        return "action_ask_feature_question"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        for i in range(len(FEATURE_QUESTIONS)):
            feature, question, responses, _ = FEATURE_QUESTIONS.iloc[i]
            if not tracker.get_slot(feature):
                break
        responses = responses.split(",")
        data = [{"label": r, "value": r} for r in responses]
        message = {"payload": "dropDown", "data": data}
        dispatcher.utter_message(text=question, json_message=message)
        return [SlotSet(key="active_feature", value=feature)]


class ActionParseResponse(Action):

    def name(self) -> Text:
        return "action_parse_response"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        response = tracker.latest_message["text"]
        feature = tracker.get_slot("active_feature")
        tracker.slots[feature] = response
        update_research_state(tracker)
        return [SlotSet(key=feature, value=response), SlotSet("active_feature", value=None)]


class ActionAskOpenQuestion(Action):

    def name(self) -> Text:
        return "action_ask_open_question"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        for i in range(len(OPEN_QUESTIONS)):
            if not tracker.get_slot(OPEN_QUESTIONS.iloc[i]["subject"]):
                feature, question = OPEN_QUESTIONS.iloc[i]
                break
        dispatcher.utter_message(text=question)
        return [SlotSet(key="active_feature", value=feature)]


class ActionFetchResults(Action):

    def name(self):
        return "action_fetch_results"

    def run(self, dispatcher, tracker, domain):
        results = get_current_results(tracker)
        print(results)
        return []


class ActionFlushSearchState(Action):

    def name(self):
        return "action_flush_search_state"

    def run(self, dispatcher, tracker, domain):
        slots_to_clear = list(
            OPEN_QUESTIONS["subject"].values) + list(FEATURE_QUESTIONS["feature"].values)
        with open("actions/research_state.json", "w") as f:
            f.write(json.dumps({"results": ""}))
        dispatcher.utter_message(text="Sure the search space has been reset")
        return [SlotSet(key=slot, value=None) for slot in slots_to_clear]


class ActionRectify(Action):
    def name(self):
        return "action_rectify"

    def run(self, dispatcher, tracker, domain):
        feature = tracker.latest_message["entities"][0]["value"]
        return [SlotSet(key=feature, value=None), FollowupAction(name="action_ask_feature_question")]


def get_current_results(tracker):
    open_knowledge = {k: tracker.slots[k]
                      for k in OPEN_QUESTIONS["subject"].values if tracker.slots[k] is not None}

    feature_knowledge = {k: tracker.slots[k]
                         for k in FEATURE_QUESTIONS["feature"].values if tracker.slots[k] is not None}
    query = " ".join(list(open_knowledge.values())) + \
        " ".join(list(feature_knowledge.values()))
    return actions.search_engine_api_wrapper.get(feature_knowledge, query=query)


def update_research_state(tracker):
    if tracker.slots["active_feature"] == "sector":
        with open("actions/research_state.json", "r") as f:
            json_decoded = json.load(f)
            json_decoded["sector_presentation"] = SECTOR_PRESENTATION[tracker.slots["sector"]]
        with open("actions/research_state.json", "w") as f:
            f.write(json.dumps(json_decoded))
    else:
        results = get_current_results(tracker)
        with open("actions/research_state.json", "r") as f:
            json_decoded = json.load(f)
            json_decoded["results"] = results
        with open("actions/research_state.json", "w") as f:
            f.write(json.dumps(json_decoded))
