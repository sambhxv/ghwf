# Copyright (c) 2025, Ambibuzz Technologies LLP and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class Temperature(Document):
	pass

class Calculator:
    def add(self, a, b):
	return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
        	raise ValueError("Cannot divide by zero")
    	return a / b
