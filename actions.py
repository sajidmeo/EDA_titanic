from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker,FormValidationAction
from rasa_sdk.events import FormValidation, SlotSet, EventType
from rasa_sdk.executor import CollectingDispatcher
import webbrowser
import csv
import re
#from twilio.rest import Client
import random
from rasa_sdk.types import DomainDict
import requests
import json
import xmltodict
#from flask import jsonify
import xml.etree.ElementTree as ET
from collections import OrderedDict


class SendingOTP(Action):
    def name(self) -> Text:
        return "sendingOTP"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        global number
        randomnumber = random.randint(1000,9999)
        print(randomnumber)
        number = randomnumber
        response = requests.post("http://site.ping4sms.com/api/smsapi?key=7d6a8fd620b4b19bad7adedd6b69dc6d&route=2&sender=COGENT&number=" + str(tracker.get_slot("number")) + "&sms=Your%20OTP%20for%20EMS%20forget%20password%20is%20"+ str(number) + "%20Please%20do%20not%20share%20it%20with%20anyone.%20Cogent%20E%20Services&templateid=1707161526688860673")

class ValidateCogentFormOTPInterview(FormValidationAction, SendingOTP):
    def name(self) -> Text:
        return "validate_voltas_form_otp"
    
    def validate_otp(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text,Any]:
        global number
        print(str(number) +":number")
        print(str(tracker.get_slot("otp")) + ":otp")
        if str(number) == str(tracker.get_slot("otp")): #and len(slot_value) == 4: #tracker.latest_message.text
            dispatcher.utter_message(text=f"OTP verified please proceed")
            return {"otp": slot_value}

        else:
            dispatcher.utter_message(text=f"Inavlid OTP, please re enter")
            return {"otp": None}

class GettingInfoVoltas(Action):
    def name(self) -> Text:
        return "fetchingFromVoltas"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        report = requests.get("http://lb.cogentlab.com//voltas/webservice.asmx/getAccountQuery?MobNo=" + str(tracker.get_slot("number")))

        report2 = xmltodict.parse(report.text)

        output_dict = json.loads(json.dumps(report2))
        global output
        output = output_dict['PropertyClass']

class SRExists(Action):
    def name(self) -> Text:
        return "SRstatusCheck"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        Exists = output['Exists']
        if Exists == "No":
            dispatcher.utter_message(text = f"Hi, looks like this is not a registered mobile number")
            buttons = [{"title": "Re-Enter Phone number", "payload": "Re-Enter Phone"}, {"title": "Create an account", "payload": "Create account"}, {"title": "End Chat", "payload": "End Chat"}, {"title": "Go to Catalogue", "payload": "Browse Catalogue"} ]
            dispatcher.utter_button_message(" Do you want to", buttons)
        else:
            Status = output['Status']
            print("Status:" + Status)
            print(type(Status)) 
            if Status == "Pending":
                dispatcher.utter_message(text = f"Hi, your request status is " + Status + " A service representative will get in touch with you shortly.")
                buttons = [{"title": "Return to Main Menu ", "payload": "Main Menu"}, {"title": "Check against another SR no.", "payload": "Existing SR"},  {"title": "End Chat", "payload": "End Chat"}]
                dispatcher.utter_button_message("Do you want to ", buttons)
            elif Status == "Open":
                dispatcher.utter_message(text = f"Hi, your request status is " + Status + " A service representative will get in touch with you shortly.")
                buttons = [{"title": "Return to Main Menu ", "payload": "Main Menu"}, {"title": "Check against another SR no.", "payload": "Existing SR"},  {"title": "End Chat", "payload": "End Chat"}]
                dispatcher.utter_button_message("Do you want to ", buttons)

            else:
                buttons = [{"title": "Open New SR", "payload": "Open New SR"}, {"title": "Check against another SR no.", "payload": "Existing SR"}]
                dispatcher.utter_button_message("Your request status is " + Status + " Do you want to", buttons)



        
class SRDetails(Action):
    def name(self) -> Text:
        return "get_SR_details"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:

        report = requests.get("http://lb.cogentlab.com/voltas/webservice.asmx/getSRQuery?srno=" + str(tracker.get_slot("SR")))

        report2 = xmltodict.parse(report.text)
        output_dict = json.loads(json.dumps(report2))
        output2 = output_dict['PropertyClass']
        Exists = output2['Exists']
        print("Exists:" + Exists)
        print(type(Exists))
        Status = output2['Status']
        if Exists == "No":
            dispatcher.utter_message(text = f"Hi, looks like the SR you entered is incorrect.")
            buttons = [{"title": "Re-Enter SR number", "payload": "Re-Enter SR"}, {"title": "End Chat", "payload": "End Chat"}]
            dispatcher.utter_button_message(" Do you want to", buttons)
            return [SlotSet("SR", None)]

        else:
            dispatcher.utter_message(text = f"Hi, the status of your SR is "+Status)
            buttons = [{"title": "Yes", "payload": "Yes, raise a reminder"}, {"title": "No", "payload": "No, don't raise a reminder."}]
            dispatcher.utter_button_message("Would you like to raise a reminder?", buttons)
            

class SRreminder(Action):
    def name(self) -> Text:
        return "SR_reminder"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:

        # report = requests.get("http://lb.cogentlab.com/voltas/webservice.asmx/getSRQuery?srno=" + str(tracker.get_slot("SR")))
        requests.post("http://lb.cogentlab.com/voltas/webservice.asmx/getFollowupDetails?srno=" + str(tracker.get_slot("SR")) +"&ID=0&Desc=FollowUp&comment=IVRFollowUp")
        report2 = xmltodict.parse(requests.text)
        print(report2)
        output_dict = json.loads(json.dumps(report2))
        output2 = output_dict['PropertyClass']
        global exists2
        exists2 = output2['Exists']


class FollowUpSR(Action):
    def name(self) -> Text:
        return "followup_SR"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        request1 = requests.get("http://lb.cogentlab.com/voltas/webservice.asmx/getFollowupDetails?srno=" + str(tracker.get_slot("SR")) +"&ID=0&Desc=FollowUp&comment=IVRFollowUp")
        report2 = xmltodict.parse(requests1.text)
        print(report2)
        output_dict = json.loads(json.dumps(report2))
        output2 = output_dict['PropertyClass']
        exists2 = output2['Exists']
        if exists2 == "Yes":
            dispatcher.utter_message(text = f"Your follow up has been successfully generated")
        else:
            dispatcher.utter_message(text = f"There was an error generating your followup request, please contact out customer service at 9999999999")

class AskWarranty(Action):
    def name(self) -> Text:
        return "ask_warranty"

    def run(
        self,
        dispatcher, 
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        if str(tracker.get_slot("Product")) == "Air Conditioner":
            buttons = [{"title": "Yes", "payload": "Yes, AC is under warranty"}, {"title": "No", "payload": "No, AC is not under warranty"}]
            dispatcher.utter_button_message("Is your AC under warranty?", buttons)
        elif str(tracker.get_slot("Product")) == "Commerical Refrigerator":
            buttons = [{"title": "Yes", "payload": "Yes, Deep Freezer is under warranty"}, {"title": "No", "payload": "No, Deep Freezer is not under warranty"}]
            dispatcher.utter_button_message("Is your Deep Freezer under warranty?", buttons)
        elif str(tracker.get_slot("Product")) == "Air Cooler":
            buttons = [{"title": "Yes", "payload": "Yes, Air Cooler is under warranty"}, {"title": "No", "payload": "No, Air Cooler is not under warranty"}]
            dispatcher.utter_button_message("Is your Air Cooler under warranty?", buttons)
        else:
            dispatcher.utter_message(text = f"Please enter a valid Voltas Product")
            return [SlotSet("Product", None)]            

class ACwarrantyYes(Action):
    def name(self) -> Text:
        return "AC_warranty_yes"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        return [SlotSet("Warranty", "Yes")]   

class ACwarrantyNo(Action):
    def name(self) -> Text:
        return "AC_warranty_no"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        return [SlotSet("Warranty", "No")]   

class DFwarrantyYes(Action):
    def name(self) -> Text:
        return "DF_warranty_yes"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        return [SlotSet("Warranty", "Yes")]   

class DFwarrantyNo(Action):
    def name(self) -> Text:
        return "DF_warranty_no"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        return [SlotSet("Warranty", "No")]   

class CoolerwarrantyYes(Action):
    def name(self) -> Text:
        return "Cooler_warranty_yes"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        return [SlotSet("Warranty", "Yes")]   
class CoolerwarrantyNo(Action):
    def name(self) -> Text:
        return "Cooler_warranty_no"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        return [SlotSet("Warranty", "No")]   
        
class Complaint(Action):
    def name(self) -> Text:
        return "set_complaint"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        return [SlotSet("req_type", "Complaint")]   

class Complaint(Action):
    def name(self) -> Text:
        return "set_maintenance"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        return [SlotSet("req_type", "Preventive Maintenance")]  

class raiseIssueComplaint(Action):
    def name(self) -> Text:
        return "raise_issue_complaint"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        report3 = requests.get("http://lb.cogentlab.com//voltas/webservice.asmx/getAccountQuery?MobNo=" + str(tracker.get_slot("number")))

        report4 = xmltodict.parse(report3.text)

        output_dict = json.loads(json.dumps(report4))
        output3 = output_dict['PropertyClass']
        requests.post("http://lb.cogentlab.com//voltas/webservice.asmx/getSRRegistration?ID=0&Sr_SubType=Breakdown&Sr_Type=Technical&Status=Open&Sub_Status=Unassigned&PCategory=" +str(tracker.get_slot("Product"))  + "&AccID="+ output3['AccountID'] + "&KeyAccName="+ output3['KeyAccount_S'] +"&SRCategory=Warranty&PLocID=" + output3['PersonalLocationId'] +"&UPBG_AppointmentDT=&LotNumber=&UPBG_Symptom="+ str(tracker.get_slot("issue")) +"&AgreementID=")
        requests3 = requests.get("http://lb.cogentlab.com//voltas/webservice.asmx/getSRRegistration?ID=0&Sr_SubType=Breakdown&Sr_Type=Technical&Status=Open&Sub_Status=Unassigned&PCategory=" +str(tracker.get_slot("Product"))  + "&AccID="+ output3['AccountID'] + "&KeyAccName="+ output3['KeyAccount_S'] +"&SRCategory=Warranty&PLocID=" + output3['PersonalLocationId'] +"&UPBG_AppointmentDT=&LotNumber=&UPBG_Symptom="+ str(tracker.get_slot("issue")) +"&AgreementID=")
        print(requests3)
        requests2 = xmltodict.parse(requests3.text)
        output_dict2 = json.loads(json.dumps(requests2))
        print(output_dict2)
        dispatcher.utter_message(text = f"Hi, your request for " + str(tracker.get_slot("Product")) + " with issue " + str(tracker.get_slot("issue")) + " has been successfully raised.")

class raiseIssueMaintenance(Action):
    def name(self) -> Text:
        return "raise_issue_maintenance"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        # report3 = requests.get("http://lb.cogentlab.com//voltas/webservice.asmx/getAccountQuery?MobNo=" + str(tracker.get_slot("number")))

        # report4 = xmltodict.parse(report3.text)

        # output_dict = json.loads(json.dumps(report4))
        # output3 = output_dict['PropertyClass']
        # requests.post("http://lb.cogentlab.com//voltas/webservice.asmx/getSRRegistration?ID=0&Sr_SubType=Preventive Maintenance&Sr_Type=Technical&Status=Open&Sub_Status=Unassigned&PCategory=" +str(tracker.get_slot("Product"))  + "&AccID="+ output3['AccountID'] + "&KeyAccName="+ output3['KeyAccount_S'] +"&SRCategory=Warranty&PLocID=" + output3['PersonalLocationId'] +"&UPBG_AppointmentDT=&LotNumber=&UPBG_Symptom=&AgreementID=")
        dispatcher.utter_message(text = f"Hi, your request for your AC's maintenance has been successfully registered.")

class ShowCatalogue(Action):
    def name(self) -> Text:
        return "show_catalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        if str(tracker.get_slot("Product")) == "Air Conditioner":
            buttons = [{"title": "Split AC", "payload": "Split Air Conditioner"}, {"title": "Window AC", "payload": "Window Air Conditioner"}]
            dispatcher.utter_button_message("Please select your Category of AC", buttons)            
            # dispatcher.utter_message(
            #     text = f"Here is your AC Catalogue",
            #     image = "https://i.imgur.com/V2d9eCy.jpeg")
            return [SlotSet("Product", None)]   
        elif str(tracker.get_slot("Product")) == "Commercial Refrigerator":
            # dispatcher.utter_message(text = f"Here is your Fridge Catalogue")
            buttons = [{"title": "Deep Freezer", "payload": "Deep Freezer"}, {"title": "Chest Cooler", "payload": "Chest Cooler"}, {"title": "Combo Cooler", "payload": "Combo Cooler"}, {"title": "Water Cooler", "payload": "Water Cooler"}, {"title": "Visi Cooler", "payload": "Visi Cooler"}, {"title": "Chocolate Cooler", "payload": "Chocolate Cooler"}]
            dispatcher.utter_button_message("Please select your Category of Commercial Refrigirator", buttons) 
            return [SlotSet("Product", None)] 
        elif str(tracker.get_slot("Product")) == "Air Cooler":
            buttons = [{"title": "Personal Cooler", "payload": "Personal Cooler"}, {"title": "Desert Cooler", "payload": "Desert Cooler"}, {"title": "Tower Cooler", "payload": "Tower Cooler"}, {"title": "Window Cooler", "payload": "Window Cooler"}]
            dispatcher.utter_button_message("Please select your Category of AC", buttons)   
            # dispatcher.utter_message(text = f"Here is your Cooler Catalogue")
            return [SlotSet("Product", None)] 
        else: 
            dispatcher.utter_message(text = f"Please enter a valid voltas Product")
            return [SlotSet("Product", None)] 

class CreateAccount(Action):
    def name(self) -> Text:
        return "create_account"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        Exists = output['Exists']
        dispatcher.utter_message(text = f"Hi, your mobile number has been successfully registered with us.")
        buttons = [{"title": "Create New SR", "payload": "Open New SR"}, {"title": "Check against existing SR", "payload": "Existing SR"},  {"title": "Browse Catalogue", "payload": "Yes, show me the Catalogue"},   {"title": "End Chat", "payload": "End Chat"}]
        dispatcher.utter_button_message("Now would you like to ", buttons)

class SetPhoneNull(Action):
    def name(self) -> Text:
        return "set_phone_null"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
        return [SlotSet("number", None)] 

class splitACcatalogue(Action):
    def name(self) -> Text:
        return "splitACcatalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
          
        dispatcher.utter_message(
            text = f"Here is your Split AC Catalogue",
            image = "https://i.imgur.com/V2d9eCy.jpeg")

class windowACcatalogue(Action):
    def name(self) -> Text:
        return "windowACcatalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
          
        dispatcher.utter_message(
            text = f"Here is your Window AC Catalogue",
            image = "https://i.imgur.com/k39zj7w.jpg")

class deepFreezercatalogue(Action):
    def name(self) -> Text:
        return "deepFreezercatalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
          
        dispatcher.utter_message(
            text = f"Here is your Deep Freezer Catalogue",
            image = "https://i.imgur.com/feiISMy.jpg")

class chestCoolercatalogue(Action):
    def name(self) -> Text:
        return "chestCoolercatalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
          
        dispatcher.utter_message(
            text = f"Here is your Chest Cooler Catalogue",
            image = "https://i.imgur.com/paMwXTW.jpg")

class comboCoolercatalogue(Action):
    def name(self) -> Text:
        return "comboCoolercatalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
          
        dispatcher.utter_message(
            text = f"Here is your Combo Cooler Catalogue",
            image = "https://i.imgur.com/w0QJV72.png")

class waterCoolercatalogue(Action):
    def name(self) -> Text:
        return "waterCoolercatalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
          
        dispatcher.utter_message(
            text = f"Here is your Water Cooler Catalogue",
            image = "https://i.imgur.com/jY9Un5U.jpg")


class visiCoolercatalogue(Action):
    def name(self) -> Text:
        return "visiCoolercatalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
          
        dispatcher.utter_message(
            text = f"Here is your Visi Cooler Catalogue",
            image = "https://i.imgur.com/1QqI6mF.png")
            

class chocoCoolercatalogue(Action):
    def name(self) -> Text:
        return "chocoCoolercatalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
          
        dispatcher.utter_message(
            text = f"Here is your Chocolate Cooler Catalogue",
            image = "https://i.imgur.com/zUpC7XT.png")


class personalCoolercatalogue(Action):
    def name(self) -> Text:
        return "personalCoolercatalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
          
        dispatcher.utter_message(
            text = f"Here is your Personal Cooler Catalogue",
            image = "https://i.imgur.com/JnfIolD.png")

class desertCoolercatalogue(Action):
    def name(self) -> Text:
        return "desertCoolercatalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
          
        dispatcher.utter_message(
            text = f"Here is your Desert Cooler Catalogue",
            image = "https://i.imgur.com/Z1adJIT.png")

class towerCoolercatalogue(Action):
    def name(self) -> Text:
        return "towerCoolercatalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
          
        dispatcher.utter_message(
            text = f"Here is your Tower Cooler Catalogue",
            image = "https://i.imgur.com/HMcDXW6.png")

class windowCoolercatalogue(Action):
    def name(self) -> Text:
        return "windowCoolercatalogue"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "Dict",
    ) -> List[Dict[Text, Any]]:
          
        dispatcher.utter_message(
            text = f"Here is your Window Cooler Catalogue",
            image = "https://i.imgur.com/tp5ZZ6v.png")


class ActionRestart(Action):

  def name(self) -> Text:
      return "action_restart"

  async def run(
      self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
  ) -> List[Dict[Text, Any]]:

      # custom behavior

      return [...]
