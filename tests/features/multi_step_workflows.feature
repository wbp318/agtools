Feature: Complex Multi-Step Workflows
  As a farm business owner
  I want to complete end-to-end business processes
  So that I can manage my farm operations efficiently

  Background:
    Given the GenFin system is fully initialized

  Scenario: Complete purchase to payment cycle
    Given I create a vendor "Farm Equipment Co"
    When I create a purchase order with items totaling $609.00
    And the PO is approved by "Manager"
    And I receive all items on the PO
    And I create a bill from the received PO
    And I post the bill
    Then accounts payable should increase by $609.00
    When I write a check to pay the bill
    Then the bill status should be "paid"
    And accounts payable should decrease by $609.00

  Scenario: Complete sales to collection cycle
    Given I create a customer "Green Valley Farms"
    When I create an estimate for $2450.00
    And the customer accepts the estimate
    And I convert the estimate to an invoice
    And I send the invoice
    Then accounts receivable should increase by $2450.00
    When I receive partial payment of $1000.00
    Then the invoice balance should be $1450.00
    When I receive final payment of $1450.00
    Then the invoice status should be "paid"

  Scenario: Month-end bank reconciliation
    Given a bank account with last reconciled balance $10000.00
    And the following transactions occurred:
      | type       | amount   |
      | deposit    | 5000.00  |
      | check      | 1200.00  |
      | deposit    | 800.00   |
      | check      | 350.00   |
    When I start reconciliation with statement balance $14250.00
    And I mark all transactions as cleared
    And I complete the reconciliation
    Then the reconciliation should succeed

  Scenario: Apply vendor credit across multiple bills
    Given a vendor with the following open bills:
      | bill_number | amount  |
      | BILL-001    | 500.00  |
      | BILL-002    | 750.00  |
    When I receive a vendor credit for $600.00
    And I apply $500.00 to BILL-001
    Then BILL-001 should be paid
    When I apply $100.00 to BILL-002
    Then BILL-002 balance should be $650.00

  Scenario: Customer credit and payment workflow
    Given a customer with an invoice for $2000.00
    When they make a payment of $1500.00
    Then the invoice balance should be $500.00
    When I issue a credit memo for $200.00
    And I apply the credit to the invoice
    Then the invoice balance should be $300.00
    When the customer pays the remaining $300.00
    Then the invoice should be fully paid

  Scenario: Batch vendor payments
    Given the following vendors with open bills:
      | vendor   | amount  |
      | Vendor A | 2000.00 |
      | Vendor B | 2500.00 |
      | Vendor C | 450.00  |
    And a bank account with balance $10000.00
    When I create batch payment for all vendors
    Then checks should total $4950.00
    And all bills should be marked as paid
    And the bank balance should be $5050.00

  Scenario: Recurring invoice generation
    Given customers with recurring services:
      | customer | monthly_amount |
      | Farm A   | 500.00         |
      | Farm B   | 750.00         |
      | Farm C   | 600.00         |
    When I generate monthly invoices
    Then 3 invoices should be created totaling $1850.00
    When I send all invoices
    Then accounts receivable should increase by $1850.00
