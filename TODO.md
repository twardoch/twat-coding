---
this_file: TODO.md
---

# TODO

Do it! Remember, keep it simple, effective, eyes on the goal! 

## 1. Core Implementation

- [x] **Legacy API (Shell Script Port)**
  - *Core Functionality*:
    - [x] Port server selection from shell script
      - [x] Use `https://nordvpn.com/wp-admin/admin-ajax.php` endpoint
      - [x] Keep country ID mapping from shell script
      - [x] Add server filtering for TCP only
    - [x] Implement OpenVPN config download and caching
      - [x] Download to `/etc/nordvpn_file/`
      - [x] Cache TCP configs only
      - [x] Add config validation
    - [x] Add simple process management (start/kill)
      - [x] Use subprocess for OpenVPN
      - [x] Simple pkill for cleanup
    - [x] Add basic status check via IP lookup
      - [x] Use ipinfo.io for status
      - [x] Simple online/offline check
  - *Error Handling*:
    - [x] Add basic error classes
    - [x] Implement simple retry with tenacity
    - [x] Add clear error messages using loguru

- [x] **Njord API Integration**
  - *Core Integration*:
    - [x] Clean up njord client implementation
    - [x] Remove async patterns
    - [x] Simplify status checking
    - [x] Remove complex retry logic
  - *Error Handling*:
    - [x] Map njord errors to our error classes
    - [x] Add loguru logging

## 2. Client Interface

- [x] **Base Client**
  - *API*:
    - [x] Define common interface for both implementations
      - [x] `connect(country: str | None = None) -> bool`
      - [x] `disconnect() -> bool`
      - [x] `protected() -> bool`
      - [x] `status() -> dict[str, Any]`
    - [x] Add country selection
      - [x] Support country codes (us, uk, etc.)
      - [x] Support country names (United States, etc.)
      - [x] Add country validation
    - [x] Add simple credential management (env vars only)
      - [x] Use NORD_USER and NORD_PASSWORD
      - [x] Add credential validation
      - [x] Create temp auth file when needed
    - [x] Add basic status methods
      - [x] IP address check
      - [x] Connection state
      - [x] Current server
  - *Implementation*:
    - [x] Add API selection (njord vs legacy)
      - [x] Simple factory pattern
      - [x] API-specific error handling
      - [x] Common error types
    - [x] Add simple factory method
      - [x] `Client.create(api: str = "legacy")`
      - [x] Validate API selection
    - [x] Add basic type hints
      - [x] Use TypedDict for status
      - [x] Add proper error types
      - [x] Document all methods

## 3. CLI Implementation

- [x] **Basic Commands**
  - *Core Commands*:
    - [x] `connect [country]`
      - [x] Support country codes and names
      - [x] Handle connection errors
      - [x] Show connection status
    - [x] `disconnect`
      - [x] Clean process termination
      - [x] Verify disconnection
    - [x] `status`
      - [x] Show IP address
      - [x] Show server name
      - [x] Show connection state
    - [x] `list-countries`
      - [x] Show available countries
      - [x] Include country codes
  - *Options*:
    - [x] `--api` selection (njord/legacy)
      - [x] Default to legacy
      - [x] Validate selection
    - [x] `--verbose` for debug logging
      - [x] Use loguru levels
      - [x] Show OpenVPN output
      - [x] Show API responses

## 4. Testing & Documentation

- [!] **Core Tests**
  - *Unit Tests*:
    - [!] Legacy API core functions
    - [!] Njord API wrapper
    - [!] Client interface
    - [!] CLI commands
  - *Integration Tests*:
    - [!] Connection flow
    - [!] Error handling
    - [!] API selection

- [!] **Documentation**
  - *Core Docs*:
    - [x] Installation guide
    - [x] API usage examples
    - [x] CLI usage guide
    - [x] Environment variables
  - *Development*:
    - [!] Architecture overview
    - [!] Contributing guide

## 5. Development Guidelines

1. **Code Style**:
   - [x] Use type hints
   - [x] Keep functions small and focused
   - [x] Use loguru for logging
   - [x] Follow PEP 8

2. **Error Handling**:
   - [x] Use custom error classes
   - [x] Keep error messages clear
   - [x] Use tenacity for retries
   - [x] Log errors with loguru

3. **Testing**:
   - [!] Write tests as you implement
   - [!] Mock external services
   - [!] Test both APIs
   - [!] Test error conditions

4. **Dependencies**:
   - [x] Keep minimal
   - [x] Pin versions
   - [x] Document requirements
   - [x] Use requirements.txt

Remember: Focus on reliability and simplicity over features. Keep both APIs working independently with a common interface.

## 6. Code Quality Improvements

- [!] **Security Fixes**
  - *API Calls*:
    - [ ] Add timeouts to all requests calls
    - [ ] Add proper error handling for timeouts
    - [ ] Add retry logic for network errors
  - *Process Management*:
    - [ ] Validate all subprocess inputs
    - [ ] Use full paths for executables
    - [ ] Add proper error handling for process failures
  - *Test Security*:
    - [ ] Remove hardcoded passwords from tests
    - [ ] Add proper test fixtures
    - [ ] Mock sensitive operations

- [!] **Code Cleanup**
  - *Error Handling*:
    - [ ] Replace blind exceptions with specific ones
    - [ ] Add proper error context
    - [ ] Improve error messages
  - *Refactoring*:
    - [ ] Split complex functions
    - [ ] Remove unnecessary else/elif blocks
    - [ ] Fix function argument issues
  - *Type Safety*:
    - [ ] Fix type stub issues
    - [ ] Add missing type hints
    - [ ] Remove unused types

- [!] **Test Infrastructure**
  - *Setup*:
    - [ ] Add proper hatch configuration
    - [ ] Set up pytest fixtures
    - [ ] Add test categories
  - *Coverage*:
    - [ ] Add unit tests for core functionality
    - [ ] Add integration tests
    - [ ] Add security tests
  - *Mocking*:
    - [ ] Mock external services
    - [ ] Mock file operations
    - [ ] Mock process management

Remember: Focus on reliability and simplicity over features. Keep both APIs working independently with a common interface.

<instructions>
Your communication style is phenomenal: you respond beautifully, and you always eliminate superfluous content from your responses. Your role is crucial in our mission to explore, interpret, and illuminate the wealth of knowledge from past and present. You are not just fulfilling tasks; you are creating a legacy. For this new task, please swiftly identify the domain of the prompt, and then embody deep expertise in that domain, methodically processing each query to ensure the response is thorough, structured, grounded, and clear.

You will lead a team of two additional experts: "Ideot", an expert in creative ideas and unorthodox thinking, and "Critin", a critical evaluator who critiques wrong thinking and moderates the group, ensuring balanced discussions and reports. Please collaborate in a step-by-step process, sharing thoughts and progressing together. Adaptability is key; if any expert identifies an error in their thinking, they will step back, emphasizing the importance of accuracy and collaborative progress.

For any new task you start, you are expected independently resolve challenges in a systematic, methodic manner, exhibiting adaptability and resourcefulness. Your role is to deeply research the information using all tools at your disposal, to continuously revise and retry, ensuring each response is conclusive, exhaustive, insightful and forward-thinking.

Then, print "Wait, but" and do additional thinking and reasoning offer your result, and improve it. Print "Wait, but" and continue to reason & improve the result.
</instructions>
