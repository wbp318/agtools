Feature: Invoice Workflow
  As a farm business owner
  I want to create and manage invoices
  So that I can bill customers and track receivables

  Background:
    Given the GenFin system is initialized
    And a customer "Smith Farm Supply" exists

  Scenario: Create and send a basic invoice
    When I create an invoice for customer "Smith Farm Supply"
    And I add a line item "Consulting Services" for $500.00
    And I save the invoice
    Then the invoice should be saved with status "Open"
    And accounts receivable should increase by $500.00

  Scenario: Apply payment to invoice
    Given an open invoice exists for "Smith Farm Supply" for $1000.00
    When I receive a payment of $1000.00
    And I apply it to the invoice
    Then the invoice status should be "Paid"
    And accounts receivable should decrease by $1000.00
    And cash should increase by $1000.00

  Scenario: Partial payment on invoice
    Given an open invoice exists for "Smith Farm Supply" for $1000.00
    When I receive a payment of $400.00
    And I apply it to the invoice
    Then the invoice status should be "Partially Paid"
    And the invoice balance due should be $600.00
    And accounts receivable should decrease by $400.00

  Scenario: Create invoice with multiple line items
    When I create an invoice for customer "Smith Farm Supply"
    And I add a line item "Seed - Corn" for $2500.00
    And I add a line item "Seed - Soybeans" for $1800.00
    And I add a line item "Delivery" for $150.00
    And I save the invoice
    Then the invoice total should be $4450.00
    And the invoice should have 3 line items
