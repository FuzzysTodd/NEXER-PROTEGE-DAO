---# GitHub Copilot Instructions

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
- [ESLint Rules for TypeScript](https://typescript-
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
- 
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
---
description: Systematic task execution workflow with proper testing and git practices for AI-assisted development
applyTo: "**/*.{js,ts,py,java,go,rs,rb,php,cs}"
---

# Task Execution and Management Workflow

## Overview

This workflow provides a systematic approach to executing development tasks generated from PRDs. It emphasizes controlled progress, proper testing, and clean git practices to ensure reliable AI-assisted development.

## Core Principles

### One Task at a Time

- **Execute one sub-task at a time** - Do not start the next sub-task until the current one is complete
- **Seek approval** - Ask for user permission before starting each new sub-task
- **Wait for confirmation** - User must respond "yes", "y", or equivalent before proceeding

### Progress Tracking

- **Update immediately** - Mark tasks as completed `[x]` as soon as they're finished
- **Maintain accuracy** - Keep the task list current and accurate
- **Document changes** - Update the "Relevant Files" section with every modification

## Task Execution Protocol

### Step 1: Task Selection

1. Identify the next available task (not blocked by dependencies)
2. Review task requirements and acceptance criteria
3. Confirm prerequisites are met
4. Ask user for permission to proceed

### Step 2: Implementation

1. **Plan the approach** - Outline implementation strategy
2. **Implement the feature** - Write code using GitHub Copilot
3. **Test locally** - Verify functionality works as expected
4. **Mark sub-task complete** - Update task list with `[x]`

### Step 3: Completion Protocol

When **all sub-tasks** under a parent task are marked `[x]`:

1. **Run full test suite**

   ```bash
   # Examples for different frameworks
   pytest                 # Python
   npm test              # Node.js
   bin/rails test        # Ruby on Rails
   cargo test            # Rust
   go test ./...         # Go
   ```

2. **Only if all tests pass** - Proceed to next steps
3. **Stage changes** - `git add .`
4. **Clean up** - Remove temporary files and code
5. **Commit with structured message** - Use conventional commit format

### Step 4: Git Commit Guidelines

Use single-line format with multiple `-m` flags:

```bash
git commit -m "feat: add payment validation logic" \
           -m "- Validates card type and expiry" \
           -m "- Adds unit tests for edge cases" \
           -m "Related to T123 in PRD"
```

#### Commit Message Structure

- **Type**: `feat`, `fix`, `refactor`, `test`, `docs`, `style`, `perf`
- **Summary**: Brief description of what was accomplished
- **Details**: Key changes and additions (use additional `-m` flags)
- **Reference**: Task number and PRD context

### Step 5: Parent Task Completion

1. Mark **parent task** as completed `[x]`
2. Update relevant files list
3. Ask user permission for next task

## Task List Management

### Status Updates

```markdown
- [x] **T001: Completed Task**
  - [x] Completed sub-task 1
  - [x] Completed sub-task 2
  
- [ ] **T002: In Progress Task**
  - [x] Completed sub-task 1
  - [ ] Current sub-task 2
  - [ ] Pending sub-task 3
```

### Relevant Files Section

Maintain an up-to-date list of all files created or modified:

```markdown
## Relevant Files
- `src/components/LoginForm.jsx` - User authentication form with validation
- `src/utils/validation.js` - Input validation helper functions
- `src/services/authService.js` - Authentication API calls
- `tests/auth.test.js` - Unit tests for authentication logic
```

## GitHub Copilot Integration

### Effective Prompting

1. **Context Setting**: Reference the current task and PRD section
2. **Specific Requests**: Ask for precise implementations
3. **Code Review**: Request validation against requirements
4. **Testing**: Generate appropriate test cases

### Example Prompts

```javascript
// Context setting
"Based on task T005 in the PRD, I need to implement user authentication..."

// Specific implementation
"Generate a login endpoint that validates email/password and returns JWT token"

// Code review
"Review this authentication middleware against the PRD security requirements"

// Testing
"Create unit tests for the login function covering success and error cases"
```

## Quality Assurance

### Before Marking Tasks Complete

- [ ] Functionality works as specified in PRD
- [ ] All edge cases are handled
- [ ] Error handling is implemented
- [ ] Code follows project conventions
- [ ] Tests are written and passing
- [ ] Documentation is updated

### Testing Strategy

1. **Unit Tests** - Test individual functions and components
2. **Integration Tests** - Test component interactions
3. **End-to-End Tests** - Test complete user workflows
4. **Manual Testing** - Verify UI/UX works as expected

## Common Execution Patterns

### Frontend Task Execution

1. Create component structure
2. Implement functionality
3. Add styling and responsive design
4. Handle user interactions and state
5. Add error handling
6. Write tests
7. Update documentation

### Backend Task Execution

1. Define API endpoints
2. Implement business logic
3. Add data validation
4. Handle errors and edge cases
5. Write unit tests
6. Test API endpoints
7. Update API documentation

### Database Task Execution

1. Design schema changes
2. Create migration scripts
3. Update models/entities
4. Test migrations
5. Verify data integrity
6. Update data access layer
7. Document schema changes

## Error Handling and Troubleshooting

### When Tests Fail

1. **Do not commit** - Fix issues before staging changes
2. **Debug systematically** - Isolate the problem
3. **Check dependencies** - Ensure all requirements are met
4. **Review PRD** - Verify implementation matches requirements
5. **Ask for help** - Request user guidance if stuck

### When Tasks Are Blocked

1. **Identify blocker** - Document what's preventing progress
2. **Communicate clearly** - Explain the issue to user
3. **Propose solutions** - Suggest alternatives or workarounds
4. **Update task list** - Mark dependencies that need resolution

## Best Practices

### Code Quality

- Follow existing code style and conventions
- Write self-documenting code with clear variable names
- Add appropriate error handling
- Include helpful code comments for complex logic
- Keep functions small and focused

### Git Practices

- Make atomic commits (one logical change per commit)
- Write clear, descriptive commit messages
- Test before committing
- Keep commit history clean and meaningful

### Documentation

- Update README files as needed
- Document API changes
- Add inline code documentation
- Keep architecture decisions recorded

### Communication

- Ask for clarification when requirements are unclear
- Provide regular progress updates
- Explain implementation decisions
- Request feedback on complex implementations

## Workflow Integration

This task execution workflow integrates with:

- **PRD Creation**: Reference PRD sections during implementation
- **Task Generation**: Follow task breakdown and dependencies
- **Code Review**: Validate implementations against PRD requirements
- **Testing**: Execute comprehensive testing strategy
- **Deployment**: Prepare code for production deployment
i grant write access what else 
- [Terraform GitHub Actions](https://github.com/hashicorp/setup-terraform)
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
- eslint.io/rules/)
- 
- [Prettier Formatter](https://prettier.io/)
# Fill in the fields below to create a basic custom agent for your repository.
# The Copilot CLI can be used for local testing: https://gh.io/customagents/cli
# To make this agent available, merge this file into the default repository branch.
# For format details, see: https://gh.io/customagents/config

name:
description:
---

# My Agent

Describe what your agent does here...
