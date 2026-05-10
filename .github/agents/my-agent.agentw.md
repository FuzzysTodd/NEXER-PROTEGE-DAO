---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name:
description:
---
name: Feature Request
description: Suggest a new Copilot instruction, prompt or chatmode pattern or improvement
title: "[FEATURE] <title>"
labels: ["Feature", "Needs Triage"]
body:
- type: checkboxes
  attributes:
    label: Is there an existing issue for this?
    description: Please search to see if an issue already exists for the feature.
    options:
    - label: I have searched the existing issues
      required: true
- type: dropdown
  id: file-type
  attributes:
    label: What type of feature is this?
    multiple: true
    options:
      - Instruction
      - Prompt
      - Chatmode
- type: textarea
  id: feature-description
  attributes:
    label: Describe the Solution
    description: A concise description of the proposed solution.
  validations:
    required: true
- type: textarea
  id: alternatives
  attributes:
    label: Describe Alternatives
    description: Mention any patterns, workarounds, or tools you've tried that help Copilot behave better.
  validations:
    required: false
- type: textarea
  id: additional-context
  attributes:
    label: Additional Context
    description: List relevant languages/frameworks (e.g., Node.js, Terraform), link to examples, or add screenshots.
  validations:
    required: false
- type: checkboxes
  id: terms
  attributes:
    label: Code of Conduct
    description: By submitting this issue, you agree to follow our [Code of Conduct](https://github.com/Code-and-Sorts/awesome-copilot-instructions/blob/main/CODE-OF-CONDUCT.md).
    options:
      - label: I agree to follow this project's Code of Conduct
        required: true
# My Agent

Describe what your agent does here...
