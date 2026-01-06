Feature: Bill Payment Workflow
  As a farm business owner
  I want to track and pay bills from vendors
  So that I can manage accounts payable

  Background:
    Given the GenFin system is initialized
    And a vendor "County Co-op" exists

  Scenario: Enter and pay a bill
    When I enter a bill from "County Co-op" for $850.00
    And I set the due date to 30 days from now
    And I save the bill
    Then the bill should be saved with status "Unpaid"
    And accounts payable should increase by $850.00
    When I pay the bill in full
    Then the bill status should be "Paid"
    And accounts payable should decrease by $850.00

  Scenario: Pay multiple bills at once
    Given I have the following unpaid bills:
      | vendor        | amount   |
      | County Co-op  | 500.00   |
      | Farm Supply   | 750.00   |
      | Fuel Plus     | 325.00   |
    When I select all bills for payment
    And I pay from the "Operating Account"
    Then all bills should be marked as "Paid"
    And the total payment should be $1575.00

  Scenario: Apply vendor credit to bill
    Given a bill exists from "County Co-op" for $1000.00
    And a vendor credit exists from "County Co-op" for $200.00
    When I pay the bill and apply the credit
    Then the cash payment should be $800.00
    And the vendor credit should be consumed
    And the bill status should be "Paid"

  Scenario: Create bill from purchase order
    Given a purchase order exists for "County Co-op" for $2500.00
    When I receive the items and create a bill
    Then a bill should be created for $2500.00
    And the purchase order status should be "Received"
