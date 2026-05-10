---
description: A chatmode for for writing clean, readable, and maintainable code following established coding guidelines.
tools: ['edit', 'runNotebooks', 'search', 'new', 'runCommands', 'runTasks', 'extensions', 'usages', 'vscodeAPI', 'problems', 'changes', 'testFailure', 'openSimpleBrowser', 'fetch', 'githubRepo', 'todos']
---

## General Principles
- Code must be **simple, direct, and expressive**.
- Always prioritize **readability and maintainability** over brevity.
- Avoid duplication and ensure all code passes tests.
- Each file, class, and function should have **one clear purpose**.

## Naming
- Use **intention-revealing, descriptive names**.
- Avoid abbreviations and misleading terms.
- Use **nouns for classes**, **verbs for functions**, **clear terms for variables**.
- Maintain **consistent naming conventions** across files.

## Functions
- Functions must be **small** and **do one thing**.
- Use **clear, descriptive names**.
- Prefer **≤ 2 parameters** (max 3).
- Avoid side effects.
- Keep a **single level of abstraction** within each function.
- Functions must **either perform an action or return data**, never both.

## Comments
- Use comments **only when code cannot express intent clearly**.
- Good comments: legal notes, rationale, TODOs, warnings.
- Bad comments: redundant, outdated, or restating what code already shows.
- Prefer self-explanatory naming and structure to reduce need for comments.

## Formatting
- Structure code like **well-written prose**.
- Group related code together; separate unrelated sections with blank lines.
- Maintain consistent **indentation and spacing**.
- Limit vertical length of functions and classes for clarity.

## Objects & Data Structures
- Encapsulate data — never expose internal structures directly.
- Use **data transfer objects** for simple data, **behavioral objects** for logic.
- Avoid `if` or `switch` statements on type; use **polymorphism**.
- Favor **composition over inheritance**.

## Error Handling
- Use **exceptions** instead of error codes.
- Don’t return or accept `null` — prefer safe defaults or option types.
- Keep **error-handling separate from main logic**.
- Always clean up resources after exceptions.

## Boundaries
- Wrap external APIs or libraries in adapter layers.
- Isolate third-party dependencies to protect against change.
- Write **tests** that capture your expectations for external systems.

## Testing
Follow the **FIRST** principles:
- Fast
- Independent
- Repeatable
- Self-validating
- Timely

Tests must be **clean, readable, and reflect real behavior**.
Never skip tests. Treat test code with the same care as production code.

## Classes
- Each class should have **a single responsibility** (SRP).
- Small and focused: one reason to change.
- Hide implementation details behind clear interfaces.
- Minimize dependencies and coupling.

## Systems
- Keep systems **modular, decoupled, and testable**.
- Use **dependency injection** to manage dependencies.
- Separate **construction** from **usage**.
- Design for **scalability and clarity**.

## Emergent Design
A clean system exhibits these traits:
1. Runs all tests.
2. Contains no duplication.
3. Expresses clear intent.
4. Minimizes the number of classes and methods.

## Code Smells (Avoid These)
- Long functions or classes.
- Duplicated code.
- Inconsistent naming.
- Magic numbers or strings.
- Overly commented or confusing code.
- Tight coupling and unclear abstractions.
- Large parameter lists.

## Clean Coder Mindset
- Treat code as **craftsmanship**, not output.
- **Refactor continually**; leave code cleaner than you found it.
- Strive for **clarity, simplicity, and correctness**.
- Generate code that another engineer can read and understand **instantly**.---
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name:
description:
---

# My Agent
---
description: A chatmode to help debug code by providing detailed error analysis and potential fixes.
tools: ['edit', 'search', 'new', 'runCommands', 'runTasks', 'extensions', 'usages', 'vscodeAPI', 'problems', 'changes', 'testFailure', 'openSimpleBrowser', 'fetch', 'githubRepo', 'todos']
---

# Purpose
You are a chatmode responsible for diagnosing and fixing software issues.

# Assessing the Problem

## Understand the Problem
- Identify what is broken — reproduce the issue.
- Gather context: error messages, logs, stack traces, and inputs.
- Examine the codebase around the failure.
- Ask:
  - What did the code intend to do?
  - What actually happened?
  - When and where does it fail?

## Reproduce Consistently
- Reproduce before theorizing; gather evidence (stack trace, logs, exact command)
- Create a minimal reproducible case.
- Fix the environment: same dependencies, data, and configuration.
- Verify you can trigger the error reliably before proceeding.

# Investigation Strategies

## Isolate the Source
- Use binary search debugging — disable or comment out sections of code to locate the fault.
- Add temporary logging or print statements to trace execution flow.
- Check inputs and outputs at key points.
- Confirm assumptions (data types, values, API responses, file paths).

## Inspect the Environment
- Check versions of dependencies, SDKs, and libraries.
- Verify configuration files and environment variables.
- Inspect network connections, permissions, or file system paths when applicable.

## Read the Error Thoroughly
- Examine stack traces from the bottom up (root cause usually last).
- Identify line numbers, function names, and modules involved.
- Match these against source code to locate the failure point.

## Validate Assumptions
- Ask: “What am I assuming that might not be true?”
- Confirm:
  - Inputs are correct and valid.
  - Functions return expected data.
  - Variables hold expected values.
  - Asynchronous or concurrent code executes as intended.

## Use Tools
- Use built-in debuggers (e.g., `pdb`, Chrome DevTools, `gdb`, VS Code debugger).
- Use logging frameworks instead of print statements for reproducibility.
- Inspect runtime state with breakpoints, watches, or REPLs.
- Employ profilers for performance or memory issues.

## Check Recent Changes
- Review recent commits, merges, or deployments.
- Compare working vs. failing versions.
- Revert or isolate new code paths introduced recently.

## Simplify
- Reduce the code to the smallest version that fails.
- Remove unrelated modules or complexity.
- This helps ensure the issue is in logic, not context.

## Form a Hypothesis
- Predict why the failure occurs.
- Test the hypothesis by making a small, controlled change.
- Observe if the behavior aligns with the prediction.

# Resolving the Issue

## Fix Carefully
- Make minimal, reversible changes.
- Re-run the full test suite after each modification.
- Validate the fix under all known scenarios.

## Prevent Regression
- Write or update unit and integration tests for the bug.
- Ensure tests fail before the fix and pass afterward.
- Add relevant assertions or logging for future detection.

## Reflect and Document
- Record root cause, fix summary, and lessons learned.
- Update documentation or comments for future maintainers.
- Clean up any debug code or temporary logs.

# Quality

## Code Quality
- Ensure the fix adheres to coding standards and best practices.
- Add or update tests to cover edge cases and prevent regressions.
- Review for performance, security, and maintainability.
- Update documentation if necessary.

# Overview Report

- Document and summarize the issue, root cause, and resolution steps.
- Highlight any changes made to the codebase.
- Provide recommendations for monitoring or future prevention.

# Guidelines

- Avoid guessing — infer from traceable evidence.
- Request missing context if critical (e.g., error output, code snippet).
- Propose multiple possible causes ranked by likelihood.
- Never overwrite working logic without justification.

- # GitHub Copilot Instructions

These instructions define how GitHub Copilot should assist with this Go project. The goal is to ensure consistent, high-quality code generation aligned with Go idioms, the chosen architecture, and our team's best practices.

## 🧠 Context

- **Project Type**: CLI Tool
- **Language**: Go
- **Framework / Libraries**: cobra, testify, charmbracelet/bubbles
- **Architecture**: Modular MVU (Model-View-Update) + Command Pattern

## 🔧 General Guidelines

- Follow idiomatic Go conventions (<https://go.dev/doc/effective_go>).
- Use named functions over long anonymous ones.
- Organize logic into small, composable functions.
- Prefer interfaces for dependencies to enable mocking and testing.
- Use `gofmt` or `goimports` to enforce formatting.
- Avoid unnecessary abstraction; keep things simple and readable.
- Use `context.Context` for request-scoped values and cancellation.

## 👾 TUI Guidelines

- **Component Structure:**
  - Each distinct UI element or view should generally be implemented as its own `bubble`.
  - Follow the standard `bubbles` pattern:
    - `Model`: Struct containing the component's state.
    - `Init()`: Returns the initial command (often `nil`).
    - `Update(msg tea.Msg)`: Handles incoming messages/events and updates the model. Returns `(tea.Model, tea.Cmd)`.
    - `View()`: Renders the component's UI as a string based on the current model state.
  - Keep `Update` functions focused; delegate complex logic to helper methods or separate functions.
  - Use `tea.BatchMsg` to batch multiple commands returned from `Update`.

- **State Management:**
  - Prefer local state within each component's `Model`.
  - For shared state or communication between components, use `tea.Msg` passing:
    - Parent components can pass messages down during their `Update`.
    - Child components can send messages up for the parent (or root) `Update` function to handle.
  - Avoid global state for TUI components. If necessary, inject shared dependencies (like services or data repositories) into the root TUI model during initialization.

- **Interaction & Messages:**
  - Define custom `tea.Msg` types (structs or simple types) for specific application events (e.g., `dataLoadedMsg`, `errorOccurredMsg`, `itemSelectedMsg`).
  - Use `tea.KeyMsg` for handling keyboard input within `Update`. Check `key.Type` or use `key.Matches`.
  - Commands (`tea.Cmd`) should be used for I/O operations (API calls, DB access, timers) to avoid blocking the `Update` loop. The results of these commands should be sent back as `tea.Msg`.

- **Styling:**
  - Use `lipgloss` for styling text, borders, layouts, etc.
  - Define reusable styles in `internal/util/styles.go` and reference them within component `View` methods.
  - Ensure styles adapt reasonably to different terminal sizes where possible.

- **Layout:**
  - Use `lipgloss` functions like `lipgloss.JoinVertical`, `lipgloss.JoinHorizontal`, and `lipgloss.Place` for arranging components.

## 📁 File Structure

Use this structure as a guide when creating or updating files:

```text
app/
  app.go
cmd/
  root.go
internal/
  controller/
  service/
  repository/
  model/
  config/
  middleware/
  utils/
pkg/
  logger/
  errors/
tests/
  unit/
  integration/
```

## 🧶 Patterns

### ✅ Patterns to Follow

- Use **Clean Architecture** and **Repository Pattern**.
- Implement input validation using Go structs and validation tags (e.g., [go-playground/validator](https://github.com/go-playground/validator)).
- Use custom error types for wrapping and handling business logic errors.
- Logging should be handled via `charmbracelet/log`.
- Use dependency injection via constructors (avoid global state).
- Keep `main.go` minimal—delegate to `internal`.

### 🚫 Patterns to Avoid

- Don’t use global state unless absolutely required.
- Don’t hardcode config—use environment variables or config files.
- Don’t panic or exit in library code; return errors instead.
- Don’t expose secrets—use `.env` or secret managers.
- Avoid embedding business logic in HTTP handlers.

## 🧪 Testing Guidelines

- Use `testing` and [testify](https://github.com/stretchr/testify) for assertions and mocking.
- Organize tests under `tests/unit/` and `tests/integration/`.
- Mock external services (e.g., DB, APIs) using interfaces and mocks for unit tests.
- Include table-driven tests for functions with many input variants.
- Follow TDD for core business logic.

## 🔁 Iteration & Review

- Review Copilot output before committing.
- Refactor generated code to ensure readability and testability.
- Use comments to give Copilot context for better suggestions.
- Regenerate parts that are unidiomatic or too complex.

## 📚 References

- [Go Style Guide](https://google.github.io/styleguide/go/)
- [Effective Go](https://go.dev/doc/effective_go)
- [Standard Go Project Layout](https://github.com/golang-standards/project-layout)
- [Testify](https://github.com/stretchr/testify)
- [Go Validator](https://github.com/go-playground/validator)
- [Charmbracelet Bubbletea Documentation](https://pkg.go.dev/github.com/charmbracelet/bubbletea)

- # GitHub Copilot Instructions

These instructions define how GitHub Copilot should assist with this Node.js TypeScript Express API project. The goal is to ensure consistent, high-quality code generation aligned with our conventions, Express best practices, and TypeScript standards.

## 🧠 Context

- **Project Type**: REST API
- **Language**: TypeScript (Node.js)
- **Framework / Libraries**: Express / Zod / dotenv / tslog / ts-node / cors
- **Architecture**: Modular / MVC / Clean Architecture / Layered Services

## 🔧 General Guidelines

- Use idiomatic TypeScript with strict type checking enabled.
- Use named `async` functions and avoid long inline callbacks.
- Validate input using Zod schemas and return structured error responses.
- Organize code with clear separation of concerns (routes → controller → service → repository).
- Use centralized error handling middleware.
- Format code with Prettier and enforce standards with ESLint.

## 📁 File Structure

Use this structure as a guide when creating or updating files:

```text
src/
  routes/
    user.routes.ts
    product.routes.ts
  controllers/
    user.controller.ts
  services/
    user.service.ts
  repositories/
    user.repository.ts
  schemas/
    user.schema.ts
  middleware/
    error.middleware.ts
    auth.middleware.ts
  utils/
  config/
  types/
tests/
  unit/
  integration/
```

## 🧶 Patterns

### ✅ Patterns to Follow

- Use `express.Router()` for grouping route handlers by domain.
- Validate request bodies and query params with Zod inside middleware or controllers.
- Return consistent JSON responses with `status`, `message`, and `data`.
- Use dependency injection for service and repository layers when needed.
- Store config and secrets in `.env` and load with `dotenv`.
- Use a logging library (e.g. `tslog`) for structured logging.
- Separate side-effect code (e.g., DB access) from pure functions.

### 🚫 Patterns to Avoid

- Don’t put business logic directly in route handlers.
- Avoid using `any` — always type inputs and outputs.
- Don’t use `console.log` in production — use a logger.
- Don’t hardcode values — pull from config or env vars.
- Avoid monolithic controllers — break down logic into services and helpers.

## 🧪 Testing Guidelines

- Use `Jest` or `Vitest` for unit and integration tests.
- Use `supertest` for HTTP layer testing.
- Mock services and DB calls to isolate controller behavior.
- Use test doubles or stubs for external APIs.
- Test Zod schemas for valid/invalid cases where applicable.

## 🧩 Example Prompts

- `Copilot, create a POST /users endpoint using Express that validates the request body with Zod.`
- `Copilot, implement a user controller that delegates to a user service and returns 201 Created.`
- `Copilot, generate a Zod schema for a product with id, name, and price.`
- `Copilot, write a middleware that handles Zod validation errors and formats a response.`
- `Copilot, create a Jest unit test for the user controller’s createUser function using mocks.`

## 🔁 Iteration & Review

- Review Copilot output with Prettier and ESLint before committing.
- Use comments to guide Copilot when generating controller logic or complex validation.
- Refactor repeated logic into shared utilities or middleware.
- Validate schema contracts and function signatures with type checking.

## 📚 References

- [Express.js Documentation](https://expressjs.com/)
- [Zod Documentation](https://zod.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [tslog Logging](https://github.com/fullstack-build/tslog)
- [dotenv Config Docs](https://github.com/motdotla/dotenv)
- [Jest Documentation](https://jestjs.io/)
- [Supertest for Express](https://github.com/visionmedia/supertest)
- [ESLint Rules for TypeScript](https://typescript-eslint.io/rules/)
- [Prettier Formatter](https://prettier.io/)
- 
# GitHub Copilot Instructions

These instructions define how GitHub Copilot should assist with this project. The goal is to ensure consistent, high-quality code generation aligned with our conventions, stack, and best practices.

## 🧠 Context

- **Project Type**: Web API / Backend Service / CLI App / Android App
- **Language**: Java
- **Framework / Libraries**: Spring Boot / Jakarta EE / Hibernate / JUnit / Maven / Gradle
- **Architecture**: MVC / Clean Architecture / Hexagonal / Microservices

## 🔧 General Guidelines

- Use Java-idiomatic patterns and follow standard conventions (JavaBeans, package structure).
- Use proper access modifiers (`private` by default).
- Always include null checks and use Optional where appropriate.
- Prefer `final` for variables that don't change.
- Format using `google-java-format` or IDE rules.
- Favor readability, testability, and separation of concerns.

## 📁 File Structure

Use this structure as a guide when creating or updating files:

```text
src/
  main/
    java/
      com/
        example/
          app/
            controllers/
            services/
            repositories/
            models/
            config/
    resources/
  test/
    java/
      com/
        example/
          app/
            unit/
            integration/
```

## 🧶 Patterns

### ✅ Patterns to Follow

- Use Dependency Injection via Spring's `@Autowired` or constructor injection.
- Apply standard annotations like `@Service`, `@Repository`, `@RestController`.
- Use DTOs for request/response payloads.
- Validate inputs with `@Valid` and Bean Validation (`javax.validation`).
- Handle exceptions using `@ControllerAdvice`.
- Log using `slf4j` and parameterized logging.
- Organize code by feature/module.
- Write clear Javadoc for public classes and methods.

### 🚫 Patterns to Avoid

- Don’t use field injection (`@Autowired` directly on fields).
- Avoid exposing entities directly to the client—use DTOs.
- Don’t hardcode values—use `application.properties` or `@Value`.
- Avoid God classes or putting too much logic in controllers.
- Don’t catch and ignore exceptions—handle or rethrow them.
- Avoid static utility classes for anything other than pure helpers.

## 🧪 Testing Guidelines

- Use `JUnit 5` and `Mockito` for unit testing.
- Use `@SpringBootTest` for integration tests.
- Follow Arrange-Act-Assert structure.
- Mock external dependencies using `@MockBean` or `@Mock`.
- Test validation, edge cases, and exception flows.

## 🧩 Example Prompts

- `Copilot, create a Spring Boot REST controller with GET and POST endpoints for books.`
- `Copilot, write a JPA repository interface for querying users by email.`
- `Copilot, define a DTO with validation annotations for user registration.`
- `Copilot, write a JUnit test for the OrderService.createOrder method using Mockito.`
- `Copilot, configure application.properties for PostgreSQL and enable debug logging.`

## 🔁 Iteration & Review

- Always review Copilot output for null safety, thread safety, and proper annotations.
- Use comments above the cursor to guide Copilot’s intent.
- Refactor repetitive or over-engineered output.
- Run linting (`Checkstyle`, `SpotBugs`, `PMD`) and formatting tools.

## 📚 References

- [Spring Boot Documentation](https://docs.spring.io/spring-boot/docs/current/reference/htmlsingle/)
- [Java Language Specification](https://docs.oracle.com/javase/specs/)
- [Java Code Conventions (Oracle)](https://www.oracle.com/java/technologies/javase/codeconventions-contents.html)
- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
- [JUnit 5 Documentation](https://junit.org/junit5/docs/current/user-guide/)
- [Mockito Documentation](https://site.mockito.org/)
- [Bean Validation (Jakarta)](https://jakarta.ee/specifications/bean-validation/)
- [SLF4J Logging](http://www.slf4j.org/manual.html)
# GitHub Copilot Instructions

These instructions define how GitHub Copilot should assist with this project. The goal is to ensure consistent, high-quality code generation aligned with our conventions, stack, and best practices.

## 🧠 Context

- **Project Type**: iOS App / macOS App / CLI Tool / Swift Package
- **Language**: Swift
- **Framework / Libraries**: SwiftUI / UIKit / Combine / Foundation / Vapor / Alamofire
- **Architecture**: MVVM / Clean Architecture / VIPER / Modular

## 🔧 General Guidelines

- Use idiomatic Swift conventions (camelCase, struct over class when possible).
- Prefer `let` over `var` for immutability.
- Use Swift’s optionals and `guard`/`if let` for safe unwrapping.
- Avoid force unwraps (`!`) unless absolutely safe and justified.
- Format using `swift-format` or SwiftLint.
- Document public methods and types using `///` doc comments.
- Leverage value types (structs, enums) and protocol-oriented design.

## 📁 File Structure

Use this structure as a guide when creating or updating files:

```text
Sources/
  App/
    Models/
    Views/
    ViewModels/
    Services/
    Utilities/
    Extensions/
Tests/
  Unit/
  Integration/
Resources/
```

## 🧶 Patterns

### ✅ Patterns to Follow

- Use MVVM for SwiftUI-based UIs.
- Use property wrappers like `@State`, `@ObservedObject`, and `@EnvironmentObject` properly.
- Leverage Combine or async/await for reactive and asynchronous logic.
- Use dependency injection through initializers or protocols.
- Break down views into reusable components.
- Validate user input using model or view model logic.
- Use enums with associated values to manage screen/view state.
- Prefer Swift’s `Codable` for JSON encoding/decoding.

### 🚫 Patterns to Avoid

- Don’t use force unwraps (`!`) unless you’re certain the value is non-nil.
- Avoid putting business logic directly inside views.
- Don’t mix UIKit and SwiftUI unnecessarily.
- Avoid deeply nested views or view models—break them into modules.
- Don’t expose internal state directly—use access control (`private`, `internal`, `public`).
- Avoid hardcoding strings or magic numbers—use constants or localization.

## 🧪 Testing Guidelines

- Use `XCTest` for unit and UI tests.
- Use `@testable import` to access internal modules when needed.
- Write snapshot/UI tests for reusable views or complex components.
- Use mock services conforming to protocols for ViewModel tests.
- Test async behavior using `XCTestExpectation` or `async/await`.

## 🧩 Example Prompts

- `Copilot, create a SwiftUI view that shows a list of users with their names and avatars.`
- `Copilot, write a model struct for a Product with name, price, and optional discount.`
- `Copilot, implement a Combine publisher that fetches data from a URL and decodes JSON.`
- `Copilot, write unit tests for the LoginViewModel using a mock AuthService.`
- `Copilot, define an enum for authentication state with associated values for success and error.`

## 🔁 Iteration & Review

- Review Copilot output for proper Swift idioms and memory safety.
- Refactor large or nested SwiftUI views into reusable components.
- Use Xcode warnings and SwiftLint to catch violations.
- Guide Copilot with comments for complex UI layout or async logic.

## 📚 References

- [The Swift Programming Language Book](https://swift.org/documentation/#the-swift-programming-language)
- [Apple SwiftUI Documentation](https://developer.apple.com/documentation/swiftui)
- [Swift.org API Guidelines](https://swift.org/documentation/api-design-guidelines/)
- [Combine Framework Guide](https://developer.apple.com/documentation/combine)
- [SwiftLint (Linter)](https://realm.github.io/SwiftLint/)
- [Vapor Web Framework](https://docs.vapor.codes/)
- [Alamofire Networking Library](https://github.com/Alamofire/Alamofire)
- [Apple XCTest Framework](https://developer.apple.com/documentation/xctest)
- [Swift Package Manager Docs](https://developer.apple.com/documentation/swift_packages/)
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
i grant write access what else
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
- [TFLint](https://github.com/terraform-linters/tflint)
- [Checkov](https://www.checkov.io/)
- [Terratest](https://terratest.gruntwork.io/)
- [GitHub Actions for Terraform](https://github.com/hashicorp/setup-terraform)
