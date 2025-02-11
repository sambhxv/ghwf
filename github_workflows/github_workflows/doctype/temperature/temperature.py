# Copyright (c) 2025, Ambibuzz Technologies LLP and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

def call_demo_api():
    request = "lololmao"
    frappe.msgprint(request)

class Temperature(Document):
	call_demo_api()
