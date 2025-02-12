# Copyright (c) 2025, Ambibuzz Technologies LLP and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TrackRecord(Document):
	pass

def update_duration(docname):
    doc = frappe.get_doc("Track Record", docname)
    if doc.units and doc.units.isdigit():
        doc.duration = int(doc.units) * 2
        doc.save()
        frappe.db.commit()
