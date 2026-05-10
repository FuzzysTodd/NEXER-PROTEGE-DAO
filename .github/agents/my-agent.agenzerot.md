---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name:
description:
---

# My Agent

Describe what your agent does here...

# GitHub Copilot Instructions

These instructions define how GitHub Copilot should assist with this Terraform + Atmos project. The goal is to ensure consistent, modular, and environment-aware infrastructure generation aligned with our team's conventions and deployment workflows.

## 🧠 Context

- **Project Type**: Cloud Infrastructure Provisioning / Platform Engineering
- **Language / Tool**: Terraform with Atmos (YAML + HCL)
- **Cloud Providers**: AWS / Azure / GCP / Kubernetes
- **Architecture**: Modular Components / Multi-Environment / GitOps / CI-Driven

## 🔧 General Guidelines

- Follow idiomatic Atmos conventions using the `components/` and `stacks/` folders.
- Use YAML stack configurations to compose environments from reusable components.
- Prefer variables and inheritance through Atmos hierarchy rather than hardcoding.
- Structure `terraform` components under `components/terraform/`, using separate modules for reusable infrastructure.
- Ensure all components are tested independently and parameterized via `inputs`.

## 📁 File Structure

Use this structure as a guide when creating or updating files:

```text
components/
  terraform/
    vpc/
    eks/
    app/
    dns/
  atmos.yaml

stacks/
  orgs/
    acme/
      tenant1/
        dev/
          us-west-2/
            vpc.yaml
            eks.yaml
            app.yaml
        staging/
        prod/

  globals/
    globals.yaml

vendor/
  <imported components from git registries>

terraform/
  <provider.tf, backend.tf, shared locals>
```

## 🧶 Patterns

### ✅ Patterns to Follow

- Define inputs in `inputs:` blocks inside stack YAML files.
- Use `vars`, `env`, and `backend` blocks to configure state and secrets.
- Break infrastructure into composable components (e.g., `vpc`, `eks`, `alb`).
- Inherit shared settings via `import:` or `globals:` in stack files.
- Use naming conventions for stacks like `<tenant>/<stage>/<region>`.
- Validate changes using `atmos terraform plan <component> -s <stack>` before apply.
- Use Atmos CLI (`atmos terraform apply`, `atmos describe`, etc.) for all workflows.

### 🚫 Patterns to Avoid

- Don’t hardcode configuration—define everything via stack inputs or shared globals.
- Avoid modifying vendor components directly—extend or wrap instead.
- Don’t run `terraform` commands directly—always use `atmos terraform`.
- Avoid deeply nested inputs in YAML—flatten and document clearly.
- Don’t create large, monolithic components—break into logical units.
- Avoid committing `.terraform` directories or local state.

## 🧪 Testing Guidelines

- Validate YAML syntax with CI linters (`yamllint`).
- Run `atmos terraform plan` on all changed components in PRs.
- Use `tflint`, `checkov`, or `tfsec` on individual components.
- Use `atmos validate stacks/` to check stack references and structure.
- Create preview environments using short-lived stacks (e.g. `pr-123/preview`).

## 🧩 Example Prompts

- `Copilot, generate an Atmos stack YAML that deploys the vpc, eks, and app components to staging/us-west-2.`
- `Copilot, create a Terraform component for an S3 bucket with versioning and encryption enabled.`
- `Copilot, write a globals.yaml that includes standard tags and default region.`
- `Copilot, define a backend configuration block in the app component using s3 and dynamodb for state.`
- `Copilot, create a GitHub Actions job that runs atmos terraform plan on all changed stacks.`

## 🔁 Iteration & Review

# GitHub Copilot Instructions

These instructions define how GitHub Copilot should assist with this Terraform project. The goal is to ensure consistent, secure, and modular infrastructure aligned with our conventions, cloud platform, and Terraform best practices.

## 🧠 Context

- **Project Type**: Cloud Infrastructure Provisioning / Platform Engineering
- **Language / Tool**: Terraform
- **Cloud Providers**: Azure / AWS / GCP / Kubernetes
- **Architecture**: Modular / Multi-environment / Remote State / GitOps

## 🔧 General Guidelines

- Use idiomatic Terraform syntax (`.tf` and `.tfvars` files).
- Follow HCL formatting using `terraform fmt`.
- Always declare variable types and add descriptions.
- Use `locals` for repeated values and naming conventions.
- Use modules to encapsulate reusable infrastructure components.
- Keep each resource file small and single-purpose.
- Prefer resource-specific files (e.g. `network.tf`, `compute.tf`) for clarity.

## 📁 File Structure

Use this structure as a guide when creating or updating files:

```text
terraform/
  modules/
    network/
    compute/
    storage/
  environments/
    dev/
      main.tf
      variables.tf
      backend.tf
    staging/
    prod/
  shared/
    providers.tf
    variables.tf
    locals.tf
    outputs.tf
```

## 🧶 Patterns

### ✅ Patterns to Follow

- Use modules to avoid duplication and enforce standardization.
- Separate environments using workspaces or folders with unique backends.
- Use `terraform.tfvars` for environment-specific values.
- Tag all resources (e.g. `project`, `env`, `owner`).
- Use `terraform output` to expose values for integration.
- Secure sensitive variables with `sensitive = true`.
- Use remote state storage with locking (e.g. S3 + DynamoDB, Azure Storage + Blob Lock).

### 🚫 Patterns to Avoid

- Don’t commit `.terraform/` or `.tfstate` files—use `.gitignore`.
- Avoid hardcoding values—use variables or locals.
- Don’t use `terraform apply` without reviewing `terraform plan`.
- Avoid overly nested or dynamic expressions that reduce readability.
- Don’t write all resources in a single file—split by concern or service.
- Avoid depending on resource ordering—use `depends_on` where required.

## 🧪 Testing Guidelines

- Use `terraform validate` and `terraform plan` to verify correctness.
- Use `tflint`, `terraform-docs`, and `checkov` for static analysis.
- Run `terraform plan` in CI for preview-only validation on PRs.
- Use `terratest` or `kitchen-terraform` for end-to-end infrastructure tests.
- Document expectations and constraints for each module.

## 🧩 Example Prompts

- `Copilot, create a Terraform module that provisions an Azure App Service with a storage account and app settings.`
- `Copilot, define input variables for a VPC module with cidr_block and public_subnets.`
- `Copilot, write an output.tf that returns the public IP of an EC2 instance.`
- `Copilot, generate a backend.tf file using Azure Storage Account with locking enabled.`
- `Copilot, write a GitHub Actions workflow that runs terraform fmt, validate, plan on PR.`

## 🔁 Iteration & Review

- Review all Copilot-generated code with `terraform validate` and `terraform plan`.
- Add inline comments before invoking Copilot to clarify resource behavior.
- Refactor repetitive blocks into modules.
- Perform manual review of IAM, firewall, or public exposure changes.
- Ensure all modules include `README.md`, `variables.tf`, `outputs.tf`.

## 📚 References

- [Terraform Language Docs](https://developer.hashicorp.com/terraform/language)
- [Terraform CLI Command Docs](https://developer.hashicorp.com/terraform/cli/commands)
- [Terraform Registry](https://registry.terraform.io/)
- [Terraform Azure Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [TFLint](https://github.com/terraform-linters/tflint)# GitHub Copilot Instructions

These instructions define how GitHub Copilot should assist with this project. The goal is to ensure consistent, high-quality code generation aligned with our conventions, stack, and best practices.

## 🧠 Context

- **Project Type**: Game Script / CLI Tool / Plugin / Embedded Config
- **Language**: Lua
- **Framework / Libraries**: LÖVE / Neovim / OpenResty / LuaSocket / Busted
- **Architecture**: Modular / Event-Driven / Data-Driven

## 🔧 General Guidelines

- Use idiomatic Lua conventions (e.g., snake_case for variables, PascalCase for modules).
- Prefer local variables and encapsulate state in tables or closures.
- Keep functions short and focused.
- Avoid deeply nested logic and long procedural files.
- Use metatables only when necessary and document their behavior.
- Format consistently (e.g., stylua or lua-fmt).
- Prefer readability over cleverness or optimization.

## 📁 File Structure

Use this structure as a guide when creating or updating files:

```text
src/
  core/
  modules/
  utils/
  config/
  assets/
tests/
  unit/
  integration/
```

## 🧶 Patterns

### ✅ Patterns to Follow

- Use `require` and module tables to organize code.
- Prefer composition over inheritance (use tables with methods).
- Use tables and closures to manage state and encapsulate behavior.
- Return module tables from Lua files to expose public APIs.
- Use assert statements and logging for debug purposes.
- For Neovim: use `vim.api.*` safely with fallback logic.

### 🚫 Patterns to Avoid

- Don’t use global variables—always declare with `local`.
- Avoid monkey patching standard libraries.
- Don’t mix logic and configuration in the same file.
- Avoid unnecessary metatable magic or side effects.
- Don’t load or execute dynamic code (`loadstring`, etc.) without strong sandboxing.
- Avoid excessive string concatenation in loops (use `table.concat`).

## 🧪 Testing Guidelines

- Use `busted` for unit testing.
- Structure tests to verify modules/functions independently.
- Use mocks or stubs for I/O or system-level dependencies.
- Validate behavior with positive, edge, and error cases.
- Keep test setup minimal—favor self-contained tests.

## 🧩 Example Prompts
# GitHub Copilot Instructions

These instructions define how GitHub Copilot should assist with this Drupal project. The goal is to ensure consistent, high-quality code generation aligned with Drupal conventions, security best practices, and our development standards.

## 🧠 Context

- **Project Type**: Content Management System / Website / Web Application
- **Platform**: Drupal 11
- **Framework / Libraries**: Symfony Components / Drupal Core APIs
- **Database**: MySQL / MariaDB
- **Backend**: PHP
- **Frontend**: Twig / HTML / CSS / JavaScript
- **Development Environment**: DDEV
- **Command runner**: just
- **Architecture**: Modular / Hook-based / Entity-driven / Service-oriented

## 🔧 General Guidelines

- Follow Drupal coding standards and best practices (PSR-2, Drupal's PHP standards).
- Use Drupal's APIs instead of direct database queries or PHP built-ins when possible.
- Implement proper access control and security measures for all functionality.
- Use dependency injection and services for reusable business logic.
- Follow the "Drupal way" - leverage existing systems rather than reinventing.
- Use `drupal/coder` for code formatting and standards compliance.
- Document all public functions with proper PHPDoc comments.
- Prefer vanilla JavaScript over jQuery - use modern ES6+ features and native DOM APIs.
- Use Drupal's JavaScript API and behaviors (`Drupal.behaviors`) for frontend functionality.

## 📁 File Structure

Use this structure as a guide when creating or updating files:

```text
web/
  modules/
    custom/
      my_module/
        src/
          Controller/
          Entity/
          Form/
          Plugin/
          Service/
        templates/
        js/
        config/
          install/
          schema/
        my_module.info.yml
        my_module.module
        my_module.routing.yml
        my_module.services.yml
        my_module.libraries.yml
  themes/
    custom/
      my_theme/
        src/
        templates/
        css/
        js/
        images/
        my_theme.info.yml
        my_theme.theme
        my_theme.libraries.yml
config/
  sync/
    core.entity_form_display.*
    core.entity_view_display.*
    views.view.*
```

## 🧶 Patterns

### ✅ Patterns to Follow

- Use Drupal's Entity API for data modeling and storage.
- Implement hook functions following naming conventions (`hook_form_alter`, `hook_theme`, etc.).
- Use Services and Dependency Injection for business logic.
- Create Configuration entities for admin-configurable functionality.
- Use Form API for all user input forms with proper validation and security.
- Implement proper caching using Cache API (`#cache` render arrays, cache tags).
- Use Translation API (`t()`, `\Drupal::translation()`) for all user-facing strings.
- Follow security best practices - sanitize output, validate input, check permissions.
- Use Render API for all HTML output (`#type`, `#theme`, render arrays).
- Create Plugin systems for extensible functionality.
- Implement JavaScript using `Drupal.behaviors` for proper initialization and AJAX compatibility.

### 🚫 Patterns to Avoid

- Don't use direct database queries - use Entity API or Database API.
- Avoid hardcoded strings - use configuration or translation functions.
- Don't output raw HTML - use render arrays and proper theming.
- Avoid bypassing Drupal's security layer or permission system.
- Don't use global variables - use dependency injection or services.
- Avoid writing to files outside of designated directories.
- Don't ignore caching - implement proper cache invalidation.
- Avoid mixing business logic with presentation layer.
- Don't use jQuery unless absolutely necessary - prefer vanilla JavaScript and modern DOM APIs.

## 🧪 Testing Guidelines

- Use PHPUnit for unit testing custom functionality.
- Write Kernel tests for testing Drupal-integrated functionality.
- Use Functional tests (BrowserTestBase) for full page testing.
- Test with SimpleTest or Drupal Test Traits for legacy compatibility.
- Mock external services and dependencies in unit tests.
- Test access control and permissions thoroughly.
- Include tests for form validation and submission.

## 🧩 Example Prompts

- `Copilot, create a custom Drupal module that adds a content type for events with date fields and location.`
- `Copilot, implement a Drupal form that collects user feedback and saves it as a custom entity.`
- `Copilot, write a Drupal hook_form_alter to add custom validation to the user registration form.`
- `Copilot, create a Drupal service that integrates with an external API and caches the results.`
- `Copilot, generate a Drupal theme template that displays a custom content type with proper field rendering.`
- `Copilot, write a Drupal configuration entity for storing API settings with a settings form.`
- `Copilot, implement a custom Drupal field type for storing and displaying social media links.`
- `Copilot, create a Drupal behavior using vanilla JavaScript to add interactive functionality to a form.`
- `Copilot, implement a JavaScript function using fetch() API to make AJAX calls to a Drupal REST endpoint.`

## 🔁 Iteration & Review

- Always validate Copilot output against Drupal coding standards using `drupal/coder`.
- Test all functionality in a local Drupal environment before committing.
- Review security implications of any custom code, especially user input handling.
- Use `drush` commands to clear caches and test configuration changes.
- Ensure all custom code follows Drupal's API patterns and conventions.
- Verify proper access control and permission checks are in place.

## 📚 References

- [Drupal API Documentation](https://api.drupal.org/)
- [Drupal Coding Standards](https://www.drupal.org/docs/develop/standards/coding-standards)
- [Drupal JavaScript Coding Standards](https://www.drupal.org/docs/develop/standards/javascript)
- [Drupal JavaScript API and Behaviors](https://www.drupal.org/docs/drupal-apis/javascript-api)
- [Managing JavaScript in Drupal](https://www.drupal.org/docs/theming-drupal/adding-stylesheets-css-and-javascript-js-to-a-drupal-theme)
- [Drupal Security Best Practices](https://www.drupal.org/docs/security-in-drupal)
- [Form API Reference](https://api.drupal.org/api/drupal/core%21core.api.php/group/form_api)
- [Entity API Documentation](https://www.drupal.org/docs/drupal-apis/entity-api)
- [Render API Documentation](https://api.drupal.org/api/drupal/core%21core.api.php/group/render)
- [Hook System Documentation](https://api.drupal.org/api/drupal/core%21core.api.php/group/hooks)
- [Services and Dependency Injection](https://www.drupal.org/docs/drupal-apis/services-and-dependency-injection)
- [Configuration API](https://www.drupal.org/docs/drupal-apis/configuration-api)
- [Testing in Drupal](https://www.drupal.org/docs/testing)
- [Drupal Console](https://drupalconsole.com/)
- [Drush Documentation](https://www.drush.org/)
- [DDEV Documentation](https://ddev.readthedocs.io/en/stable/)
- [Just a command runner](https://github.com/casey/just)
- `Copilot, create a Lua module that exposes two functions: add and subtract.`
- `Copilot, implement a timer system using LÖVE callbacks.`
- `Copilot, write a Neovim Lua config that maps <leader>f to :Telescope find_files.`
- `Copilot, write a test using busted for a function that reverses a string.`
- `Copilot, create a config loader that reads a Lua table from a file.`

## 🔁 Iteration & Review

- Always review Copilot output for global leakage or misused metatables.
- Refactor output to follow Lua idioms and avoid verbose patterns.
- Use comments to describe intent if generating complex logic.
- Test all modules with `busted` before accepting new Copilot code.

## 📚 References

- [Programming in Lua (Official Book)](https://www.lua.org/pil/)
- [Lua 5.4 Reference Manual](https://www.lua.org/manual/5.4/)
- [LÖVE 2D Documentation](https://love2d.org/wiki/Main_Page)
- [Busted Testing Framework](https://github.com/lunarmodules/busted)
- [Stylua Formatter](https://github.com/JohnnyMorganz/StyLua)
- 
- [Checkov](https://www.checkov.io/)
- [Terratest](https://terratest.gruntwork.io/)
- [GitHub Actions for Terraform](https://github.com/hashicorp/setup-terraform)

- 

- Review all stack and component changes via `atmos terraform plan`.
- Keep stack files small and focused; split by component when needed.
- Refactor stack duplication into `import:`ed globals or partials.
- Validate all inputs are documented, typed, and overridable.

## 📚 References

- [Atmos Documentation](https://atmos.tools/cli)
- [Terraform Language Docs](https://developer.hashicorp.com/terraform/language)
- [Terraform Best Practices](https://atmos.tools/best-practices/terraform/)
- [Atmos Stack Cheatsheet](https://atmos.tools/cheatsheets/stacks)
- [TFLint](https://github.com/terraform-linters/tflint)
- [Checkov](https://www.checkov.io/)
- [Yamllint](https://yamllint.readthedocs.io/)
- [Terraform GitHub Actions](https://github.com/hashicorp/setup-terraform)
