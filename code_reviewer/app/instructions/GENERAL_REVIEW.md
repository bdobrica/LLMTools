# Code Review Instructions

These instructions define how reviews should be conducted in this repository.  
Reviews are based on the **git diff** and **Pyright** output, guided by core principles, and should remain concise and actionable.

---

## Inputs
- **Required:** `git diff` (PR/MR changes only) and **Pyright** report.
- **Optional:** PR title/description, related issue/acceptance criteria, CI results.

---

## Review Workflow

1. **Frame the change**
   - Identify change type (bugfix | feature | refactor | chore | hotfix).
   - Note public surface/API and data shape changes.

2. **Pyright triage**
   - **Blocker:** type errors, unsafe casts, definite `None`.
   - **Required:** important but not blocking compilation.
   - **Nice-to-have:** style or clarity improvements.

Perfect — here’s an expanded **Markdown version** of the **Principle pass** section, enriched with the details and examples you provided, formatted consistently so you can drop it into your existing `CODE_REVIEW.md`:

````markdown
3. **Principle pass (in order of importance)**

During review, check whether the changes align with these principles. Each principle includes a short summary, positive examples, and common mistakes.

3.1. **KISS – Keep It Simple, Stupid**
**Summary**: Encourage the simplest approach that meets the requirements—avoid unnecessary complexity.

    ✅ **Good**
    ```python
    def square(x):
        return x * x
    ````

    ❌ **Bad**

    ```python
    # Overly complex with unnecessary abstraction
    class Squarer:
        def __init__(self, factor=2):
            self.factor = factor
        def compute(self, x):
            return x ** self.factor
    ```

3.2. **YAGNI – You Ain’t Gonna Need It**
**Summary**: Don’t add features or code that aren’t required now.

    ✅ **Good**

    ```python
    def send_email(user_email, message):
        # send email logic
        pass
    ```

    ❌ **Bad**

    ```python
    # Prematurely supporting future features
    def send_email(user_email, message, cc=None, bcc=None, attachments=None, priority='normal'):
        pass
    ```

3.3. **Single Responsibility Principle (SRP)**
**Summary**: A class or function should have exactly one reason to change.

    ✅ **Good**

    ```python
    class Authenticator:
        def authenticate(self, user, password): ...
    class Logger:
        def log(self, message): ...
    ```

    ❌ **Bad**

    ```python
    class UserManager:
        def authenticate(self, user, password): ...
        def register(self, user_info): ...
        def log(self, message): ...
    ```

3.4. **Open/Closed Principle (OCP)**
**Summary**: Modules should be open for extension but closed for modification.

    ✅ **Good**

    ```python
    class Shape: ...
    class Circle(Shape): ...
    def total_area(shapes):
        return sum(s.area() for s in shapes)
    ```

    ❌ **Bad**

    ```python
    # Adding a new shape requires editing this function
    def total_area(shapes):
        for s in shapes:
            if isinstance(s, Circle): ...
            elif isinstance(s, Square): ...
    ```

3.5. **Liskov Substitution Principle (LSP)**
**Summary**: Subtypes must be substitutable for their base types without breaking expectations.

    ✅ **Good**

    ```python
    class Bird:
        def fly(self): ...
    class Sparrow(Bird):
        def fly(self): print("Flies")
    ```

    ❌ **Bad**

    ```python
    class Ostrich(Bird):  # Ostrich can’t fly
        def fly(self): raise NotImplementedError
    ```

3.6. **Interface Segregation Principle (ISP)**
**Summary**: Don’t force classes to implement methods they don’t need.

    ✅ **Good**

    ```python
    class IPrinter: ...
    class IScanner: ...
    class MultiFuncPrinter(IPrinter, IScanner): ...
    ```

    ❌ **Bad**

    ```python
    class IAllInOne:
        def print(self): ...
        def scan(self): ...
        def fax(self): ...
    ```

3.7. **Law of Demeter (LoD)**
**Summary**: “Only talk to your immediate friends”—avoid long chains of method calls.

    ✅ **Good**

    ```python
    class Car:
        def __init__(self, engine): self._engine = engine
        def start(self): self._engine.start()
    ```

    ❌ **Bad**

    ```python
    class Car:
        def check(self):
            return self.engine.fuel_tank.level.get_percent()  # deep chain
    ```

3.8. **Dependency Inversion Principle (DIP)**
**Summary**: High-level modules should depend on abstractions, not concrete classes.

    ✅ **Good**

    ```python
    class Database: ...
    class SQLDatabase(Database): ...
    class App:
        def __init__(self, db: Database): self._db = db
    ```

    ❌ **Bad**

    ```python
    class App:
        def __init__(self):
            self._db = SQLDatabase()  # tightly coupled
    ```

3.9. **Composition over Inheritance**
**Summary**: Prefer composing objects to share behavior rather than deep inheritance.

    ✅ **Good**

    ```python
    class Engine: ...
    class Car:
        def __init__(self, engine): self.engine = engine
        def start(self): self.engine.start()
    ```

    ❌ **Bad**

    ```python
    class Car(Engine):  # incorrect inheritance
        pass
    ```

3.10. **Don’t Repeat Yourself (DRY)**
**Summary**: Avoid duplication; centralize logic.

    ✅ **Good**

    ```python
    def compute_tax(amount, rate=0.1): return amount * rate
    def total_price(price, tax_rate=0.1):
        return price + compute_tax(price, tax_rate)
    ```

    ❌ **Bad**

    ```python
    def total_price(price): return price + price * 0.1
    def other_price(price): return price + price * 0.1  # duplicate
    ```


4. **Quality passes**
   - **Robustness:** validate inputs, handle errors, timeouts/retries, resource cleanup, concurrency safety.
   - **Maintainability:** clear names, small functions, docstrings/types, comments explain *why*, minimal global state.
   - **Security:** input validation, secret handling, authorization checks, safe path/network/command usage, trusted crypto libraries.

5. **Tests**
   - Verify tests exist for changed behavior and edge cases.
   - Suggest focused, deterministic, fast tests.

---

## Comment Style

Each comment should include:

- **Title:** keyword + area (e.g., *KISS: simplify construction of X*).
- **Severity:** **Blocker** | **Required** | **Nice-to-have**.
- **Rationale:** tie to principle or quality axis.
- **Suggestion:** concrete patch or minimal diff.

**Example:**
- **KISS (Required):** Constructor builds three caches but only one is used.  
  *Why:* Simplifies design (#1).  
  *Suggestion:* Remove unused `fooCache` and `barCache`; lazily init `bazCache`.

---

## Decision Criteria

- **Approve:** No blockers; Pyright clean or only Nice-to-have issues; tests adequate.
- **Approve w/ nits:** Only Nice-to-have comments.
- **Request changes:** Required issues unaddressed, missing tests, Pyright non-blockers affecting safety/maintainability.
- **Block:** Any Blocker (type errors, security flaws, contract breakage).

---

## Pyright Handling

- **Blocker:**  
  - `reportGeneralTypeIssues`, `reportOptionalMemberAccess`, unsafe `Any`.  
- **Required:**  
  - Missing/incorrect annotations on public APIs.  
  - Incomplete `Protocol`/`TypedDict`.  
- **Nice-to-have:**  
  - Redundant types, opportunities to tighten `Literal`/`Final`.

Always propose the **smallest fix** consistent with **KISS (#1)** and **YAGNI (#2)**.
