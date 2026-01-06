Feature: Bank Reconciliation
  As a farm business owner
  I want to reconcile my bank accounts
  So that I can ensure my records match the bank

  Background:
    Given the GenFin system is initialized
    And a bank account "Operating Account" exists
    And the last reconciled balance was $10000.00

  Scenario: Complete bank reconciliation
    Given the statement ending balance is $12500.00
    And I have the following cleared transactions:
      | type    | amount   | cleared |
      | deposit | 5000.00  | yes     |
      | check   | 1500.00  | yes     |
      | check   | 800.00   | yes     |
      | deposit | 200.00   | no      |
      | check   | 400.00   | no      |
    When I mark the cleared transactions
    And I finish the reconciliation
    Then the reconciliation should succeed
    And the difference should be $0.00
    And the new reconciled balance should be $12500.00

  Scenario: Reconciliation with outstanding items
    Given the statement ending balance is $8000.00
    And there are 2 outstanding checks totaling $1500.00
    And there is 1 deposit in transit for $500.00
    When I complete the reconciliation
    Then the book balance should be $9000.00
    And outstanding items should be tracked

  Scenario: Add bank fee during reconciliation
    Given I am reconciling the account
    And the bank charged a $25.00 service fee
    When I add the bank fee expense
    Then the fee should be recorded as an expense
    And the account balance should decrease by $25.00

  Scenario: Add interest income during reconciliation
    Given I am reconciling the account
    And the bank paid $15.50 interest
    When I add the interest income
    Then the interest should be recorded as income
    And the account balance should increase by $15.50
