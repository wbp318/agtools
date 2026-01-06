Feature: Concurrency and Race Condition Tests
  As a system administrator
  I want to ensure the system handles concurrent operations correctly
  So that data integrity is maintained under load

  Background:
    Given the GenFin system is initialized for concurrent testing

  Scenario: Concurrent payments to same invoice
    Given a customer with an invoice for $1000.00
    When two payments of $500.00 are applied simultaneously
    Then the invoice should be fully paid
    And the total payments should equal $1000.00
    And no duplicate payments should exist

  Scenario: Concurrent check number assignment
    Given a bank account with next check number 1001
    When 5 checks are created simultaneously
    Then each check should have a unique number
    And check numbers should be 1001 through 1005
    And no duplicate check numbers should exist

  Scenario: Concurrent bill payments from same account
    Given a bank account "Shared Account" with balance $10000.00
    And 3 vendors with bills of $2000.00 each
    When all bills are paid simultaneously
    Then all payments should succeed
    And the account balance should be $4000.00
    And no overdraft should occur

  Scenario: Concurrent invoice creation for same customer
    Given a customer "Busy Customer"
    When 3 invoices are created simultaneously
    Then all invoices should have unique numbers
    And all invoices should be linked to the customer
    And customer balance should reflect all invoices

  Scenario: Concurrent reconciliation attempts
    Given a bank account "Reconcile Test"
    When two users try to start reconciliation simultaneously
    Then only one reconciliation should be active

  Scenario: Concurrent deposit and withdrawal
    Given a bank account with balance $5000.00
    When a deposit of $1000.00 and withdrawal of $500.00 occur simultaneously
    Then the final balance should be $5500.00
    And both transactions should be recorded

  Scenario: Concurrent vendor credit application
    Given a vendor with credit of $500.00
    And two bills of $300.00 each
    When the credit is applied to both bills simultaneously
    Then total credit applied should not exceed $500.00
    And at least one application should succeed

  Scenario: Concurrent customer creation with same name
    When two customers named "Duplicate Farm" are created simultaneously
    Then both should be created with unique IDs

  Scenario: Concurrent PO approval
    Given a purchase order awaiting approval
    When two managers try to approve simultaneously
    Then the PO should be approved once
    And only one approval should be recorded

  Scenario: Concurrent bank transfer operations
    Given account "A" with $10000.00 and account "B" with $5000.00
    When transfers occur simultaneously:
      | from | to | amount  |
      | A    | B  | 2000.00 |
      | B    | A  | 1000.00 |
    Then account "A" should have $9000.00
    And account "B" should have $6000.00
    And all transfers should be recorded

  Scenario: High volume invoice processing
    Given 100 customers exist
    When 100 invoices are created in rapid succession
    Then all invoices should be created successfully
    And all invoice numbers should be unique
    And system should maintain performance

  Scenario: Concurrent void operations
    Given a check that is being printed
    When a void request comes during printing
    Then the operation should be handled gracefully
    And the check should end in a consistent state

  Scenario: Database lock handling
    Given multiple operations targeting same records
    When operations execute concurrently
    Then deadlocks should be avoided or handled
    And all operations should eventually complete
    And data integrity should be maintained
