Feature: Check Writing Workflow
  As a farm business owner
  I want to write and print checks
  So that I can pay vendors and track expenses

  Background:
    Given the GenFin system is initialized
    And a bank account "Operating Account" exists with balance $50000.00
    And a vendor "Equipment Dealer" exists

  Scenario: Write a check to vendor
    When I write a check to "Equipment Dealer" for $1250.00
    And I assign it to expense account "Equipment Repairs"
    And I save the check
    Then the check should be saved with next check number
    And the bank balance should decrease by $1250.00
    And expenses should increase by $1250.00

  Scenario: Write check with multiple expense lines
    When I write a check to "County Co-op"
    And I add expense line "Fertilizer" for $3500.00
    And I add expense line "Seed" for $2800.00
    And I add expense line "Chemicals" for $1200.00
    And I save the check
    Then the check total should be $7500.00
    And the check should have 3 expense lines

  Scenario: Void a check
    Given a check #1001 exists for $500.00
    When I void the check
    Then the check status should be "Void"
    And the bank balance should increase by $500.00
    And the expense should be reversed

  Scenario: Print checks
    Given I have 3 unprinted checks
    When I select all for printing
    And I print using "professional_voucher" format
    Then all checks should be marked as printed
    And print dates should be recorded
