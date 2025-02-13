// Copyright (c) 2025, Ambibuzz Technologies LLP and contributors
// For license information, please see license.txt

frappe.ui.form.on("Temperature", {
	refresh(frm) {
    		console.log(frm.doc);
	},
});

class Calculator {
  constructor() {
    this.currentValue = 0;
    this.operator = null;
    this.operand = null;
  }

  clear() {
    this.currentValue = 0;
    this.operator = null;
    this.operand = null;
  }

  setOperand(value) {
    this.operand = value;
  }

  setOperator(operator) {
    if (this.operand !== null) {
      this.evaluate();
    }
    this.operator = operator;
    this.operand = this.currentValue;
    this.currentValue = 0;
  }

  appendNumber(number) {
    this.currentValue = this.currentValue * 10 + number;
  }

  evaluate() {
    if (this.operator && this.operand !== null) {
      switch (this.operator) {
        case '+':
          this.currentValue = this.operand + this.currentValue;
          break;
        case '-':
          this.currentValue = this.operand - this.currentValue;
          break;
        case '*':
          this.currentValue = this.operand * this.currentValue;
          break;
        case '/':
          if (this.currentValue !== 0) {
            this.currentValue = this.operand / this.currentValue;
          } else {
            throw new Error("Division by zero");
          }
          break;
      }
      this.operator = null;
      this.operand = null;
    }
    return this.currentValue;
  }
}
