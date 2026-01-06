Feature: Error Handling Scenarios
  As a user
  I want the system to properly handle error conditions
  So that data integrity is maintained and I receive clear error messages

  Background:
    Given the GenFin system is initialized

  Scenario: Create invoice for non-existent customer
    When I try to create an invoice for customer "INVALID-ID"
    Then I should receive an error "Customer not found"
    And no invoice should be created

  Scenario: Apply payment exceeding invoice balance
    Given a customer exists with an invoice for $500.00
    When I try to apply a payment of $600.00 to the invoice
    Then I should receive an error "Payment amount exceeds balance"

  Scenario: Void invoice with payments applied
    Given a customer exists with an invoice for $1000.00
    And a payment of $400.00 has been applied
    When I try to void the invoice
    Then I should receive an error "Cannot void invoice with payments"

  Scenario: Create bill for non-existent vendor
    When I try to create a bill for vendor "INVALID-VENDOR-ID"
    Then I should receive an error "Vendor not found"

  Scenario: Pay bill exceeding balance due
    Given a vendor exists with a bill for $750.00
    When I try to pay $900.00 on the bill
    Then I should receive an error "Payment amount exceeds balance"

  Scenario: Void bill with payments
    Given a vendor exists with a bill for $1500.00
    And a payment of $500.00 has been made
    When I try to void the bill
    Then I should receive an error "Cannot void bill with payments"

  Scenario: Create check on disabled account
    Given a bank account with check printing disabled
    When I try to create a check on that account
    Then I should receive an error "Check printing not enabled"

  Scenario: Void a cleared check
    Given a bank account with a cleared check
    When I try to void the cleared check
    Then I should receive an error "Cannot void a cleared check"

  Scenario: Reconciliation with discrepancy
    Given a bank account "Test Account" with balance $10000.00
    And I record a deposit of $1000.00
    When I start reconciliation with statement balance $12500.00
    And I complete the reconciliation
    Then the reconciliation should report a discrepancy

  Scenario: Apply credit to wrong customer invoice
    Given customer "Customer A" with a credit of $200.00
    And customer "Customer B" with an invoice of $500.00
    When I try to apply Customer A credit to Customer B invoice
    Then I should receive an error "Credit and invoice must be for the same customer"

  Scenario: Apply vendor credit to wrong vendor bill
    Given vendor "Vendor A" with a credit of $300.00
    And vendor "Vendor B" with a bill of $600.00
    When I try to apply Vendor A credit to Vendor B bill
    Then I should receive an error "Credit and bill must be for the same vendor"

  Scenario: Transfer from non-existent account
    Given a bank account "Target Account" exists
    When I try to transfer from "INVALID-SOURCE" to "Target Account"
    Then I should receive an error "Source account not found"

  Scenario: Receive items on non-approved PO
    Given a vendor with a draft purchase order
    When I try to receive items on the draft PO
    Then I should receive an error "PO must be approved before receiving"

  Scenario: Create ACH batch on non-ACH account
    Given a bank account without ACH enabled
    When I try to create an ACH batch on that account
    Then I should receive an error "ACH not enabled for this account"
