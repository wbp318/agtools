Feature: Integration Tests with Backend Services
  As a developer
  I want to test that workflows properly integrate with actual backend services
  So that I can ensure end-to-end functionality works correctly

  Background:
    Given the GenFin services are initialized and connected

  Scenario: Full invoice lifecycle with actual service
    Given I create a customer "ABC Farm Supply" via the receivables service
    When I create an invoice for the customer with the following lines:
      | description        | quantity | unit_price |
      | Seed Corn          | 10       | 250.00     |
      | Fertilizer         | 5        | 180.00     |
    And I send the invoice
    Then the invoice should be posted with a journal entry
    And accounts receivable should reflect the invoice total
    When I receive payment for the full invoice amount
    Then the invoice status should be "paid"

  Scenario: Customer credit memo integration
    Given I create a customer "XYZ Farms" via the receivables service
    And I create and send an invoice for $1500.00
    When I create a credit memo for $200.00
    Then the credit should have a journal entry
    When I apply the credit to the invoice
    Then the invoice balance should be $1300.00

  Scenario: Full bill lifecycle with actual service
    Given I create a vendor "Equipment Dealer Inc" via the payables service
    When I create a bill for the vendor with the following lines:
      | description        | quantity | unit_price |
      | Tractor Parts      | 3        | 450.00     |
      | Oil Filter         | 6        | 25.00      |
    And I post the bill
    Then the bill should have a journal entry
    And accounts payable should reflect the bill total
    When I pay the bill in full via check
    Then the bill status should be "paid"

  Scenario: Purchase order to bill conversion
    Given I create a vendor "Seed Company" via the payables service
    When I create a purchase order for $3500.00
    And I approve the purchase order
    And I receive the items on the purchase order
    And I convert the PO to a bill
    Then a bill should be created for the received amount

  Scenario: Check creation with bank balance update
    Given I create a bank account "Operating Account" with balance $50000.00
    When I create a check for $1500.00 to "Vendor ABC"
    Then the bank account balance should decrease by $1500.00
    And a bank transaction should be recorded

  Scenario: Bank transfer between accounts
    Given I create a bank account "Account A" with balance $20000.00
    And I create a bank account "Account B" with balance $5000.00
    When I transfer $3000.00 from "Account A" to "Account B"
    Then "Account A" balance should be $17000.00
    And "Account B" balance should be $8000.00

  Scenario: Bank reconciliation integration
    Given I create a bank account "Reconcile Account" with balance $25000.00
    And I record a deposit of $5000.00
    And I record a check for $1200.00
    When I start reconciliation with statement balance $28800.00
    And I mark transactions as reconciled
    And I complete the reconciliation
    Then the reconciliation should succeed
