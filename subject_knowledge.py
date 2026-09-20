"""Small offline tutor dataset used when no external LLM is configured."""

SUBJECT_KNOWLEDGE = {
    "python": {
        "improve": (
            "Improve code by making one small change at a time: give variables "
            "clear names, keep functions focused, remove duplication, validate "
            "inputs, and add tests for normal and edge cases."
        ),
        "loop": (
            "Python loops repeat a block over an iterable. Use `for item in items` "
            "when you know what to iterate; use `while condition` when repetition "
            "depends on a condition. Make sure a while loop changes state so it ends."
        ),
        "list": (
            "Python lists are zero-indexed and mutable. `items[0]` is the first "
            "element, while `items[-1]` is the last. Check `if items` before "
            "accessing an element when an empty list is possible."
        ),
        "function": (
            "A Python function groups reusable logic. Parameters receive inputs, "
            "`return` sends a value back, and reaching the end without return gives None."
        ),
        "recursion": (
            "Recursion solves a problem by calling the same function on a smaller "
            "input. Every recursive function needs a base case and a step that "
            "moves toward it; without either, it can recurse forever."
        ),
        "dictionary": (
            "A Python dictionary stores key-value pairs. Lookup by key is O(1) on "
            "average, and `dict.get(key)` is useful when a key may be missing."
        ),
    },
    "java": {
        "loop": (
            "Java loops repeat work with for, while, or do-while. A for loop usually "
            "has initialization, a condition, and an update; forgetting the update "
            "can create an infinite loop."
        ),
        "null": (
            "A Java NullPointerException means a reference is null when code uses it. "
            "Trace where it is assigned, validate required inputs, and guard optional "
            "values before calling methods on them."
        ),
        "class": (
            "A Java class defines state and behavior. Fields hold state, constructors "
            "initialize objects, and methods operate on that state."
        ),
        "exception": (
            "Java exceptions represent unusual conditions. Catch only errors you "
            "can handle, keep the specific exception type, and use finally for "
            "cleanup that must happen."
        ),
        "inheritance": (
            "Java inheritance lets a subclass reuse and specialize a superclass. "
            "Prefer small interfaces and composition when inheritance would create "
            "a rigid hierarchy."
        ),
    },
    "c programming": {
        "pointer": (
            "A C pointer stores an address. Use `&value` to obtain an address and "
            "`*pointer` to dereference it. Always initialize pointers and never "
            "dereference NULL or memory that is out of scope."
        ),
        "array": (
            "C arrays are contiguous and zero-indexed. Valid indexes are 0 through "
            "length - 1; accessing beyond that range is undefined behavior."
        ),
        "memory": (
            "C memory allocated with malloc belongs to the program until free is "
            "called. Match every successful allocation with one free and avoid using "
            "the pointer after freeing it."
        ),
        "struct": (
            "A C struct groups related fields into one value. Access fields with a "
            "dot for a value and an arrow for a pointer to a struct."
        ),
    },
    "algorithms": {
        "search": (
            "Binary search requires sorted data. Compare the middle value, discard "
            "the half that cannot contain the target, and repeat in O(log n) time."
        ),
        "sort": (
            "Sorting arranges values according to an ordering. Merge sort and heap "
            "sort are O(n log n), while a well-partitioned quicksort is O(n log n) "
            "on average."
        ),
        "complexity": (
            "Big-O describes how work grows with input size. Count the dominant "
            "operation and ignore constants; nested independent loops often produce "
            "O(n squared), while halving the search space produces O(log n)."
        ),
        "recursion": (
            "Recursive algorithms need a base case and a smaller recursive case. "
            "For example, factorial(n) returns 1 at n=0 and otherwise returns "
            "n * factorial(n - 1)."
        ),
        "graph": (
            "BFS explores a graph level by level with a queue, while DFS explores "
            "a path with recursion or a stack. Mark visited nodes to avoid cycles."
        ),
    },
    "javascript": {
        "async": (
            "JavaScript async functions return Promises. Use await inside an "
            "async function, handle failures with try/catch, and use Promise.all "
            "when independent requests can run together."
        ),
        "closure": (
            "A JavaScript closure is a function that retains access to variables "
            "from its outer scope. This is useful for factories and callbacks, "
            "but long-lived closures can retain more state than intended."
        ),
        "undefined": (
            "undefined usually means a value was not assigned or a property is "
            "missing. Check the property path, initialize state, and use optional "
            "chaining only when a missing value is valid."
        ),
    },
    "typescript": {
        "type": (
            "TypeScript checks types before JavaScript runs. Prefer precise object "
            "and function types, narrow unknown values with guards, and avoid "
            "using any unless the boundary is genuinely untyped."
        ),
        "interface": (
            "A TypeScript interface describes the shape of a value. It improves "
            "editor and compiler feedback but does not validate data at runtime, "
            "so external input still needs runtime validation."
        ),
    },
    "sql": {
        "join": (
            "A SQL JOIN combines rows using a related condition. Check the join "
            "keys and grain first: a one-to-many join can multiply rows. Use "
            "GROUP BY only after confirming the intended result grain."
        ),
        "index": (
            "A database index can speed up selective filters and joins, but it "
            "costs storage and slows writes. Index columns used frequently in "
            "WHERE, JOIN, or ORDER BY clauses after checking query plans."
        ),
        "transaction": (
            "A transaction groups changes into an all-or-nothing unit. Commit "
            "only after all required operations succeed and roll back on failure."
        ),
    },
    "go": {
        "goroutine": (
            "A Go goroutine is a lightweight concurrent function. Coordinate "
            "goroutines with channels or synchronization, and ensure every "
            "goroutine has a clear way to stop."
        ),
        "pointer": (
            "A Go pointer stores the address of a value. Use pointers when shared "
            "mutation or avoiding a copy matters, and check nil before dereferencing."
        ),
    },
    "rust": {
        "ownership": (
            "Rust ownership gives each value one owner. Moving transfers ownership, "
            "borrowing gives temporary access, and the borrow checker prevents "
            "invalid references at compile time."
        ),
        "borrow": (
            "A Rust borrow is a reference to a value without taking ownership. "
            "Many immutable borrows or one mutable borrow are allowed, but not "
            "both at the same time."
        ),
    },
}


def offline_answer(message: str, subject: str | None) -> str:
    text = " ".join(message.lower().split())
    normalized_subject = (subject or "").strip().lower()
    groups = []
    if normalized_subject:
        groups.append(SUBJECT_KNOWLEDGE.get(normalized_subject, {}))
    for name, entries in SUBJECT_KNOWLEDGE.items():
        if name != normalized_subject:
            groups.append(entries)

    phrase_aliases = {
        "binary search": "search",
        "null pointer": "null",
        "nullpointerexception": "null",
        "object oriented": "class",
        "time complexity": "complexity",
        "space complexity": "complexity",
        "key value": "dictionary",
        "hash map": "dictionary",
        "linked list": "array",
        "improve my code": "improve",
        "write better code": "improve",
        "debug this": "debug",
        "async await": "async",
        "promise": "async",
        "null pointer exception": "null",
        "sql join": "join",
        "database index": "index",
        "database transaction": "transaction",
        "goroutines": "goroutine",
        "go routine": "goroutine",
        "memory ownership": "ownership",
        "borrow checker": "borrow",
    }
    for phrase, keyword in phrase_aliases.items():
        if phrase in text:
            for entries in groups:
                if keyword in entries:
                    return _format_answer(entries[keyword])

    for entries in groups:
        for keyword, answer in entries.items():
            if keyword in text.split() or f"{keyword} " in text or f" {keyword}" in text:
                return _format_answer(answer)

    if any(word in text.split() for word in ("debug", "error", "bug", "wrong", "fix")):
        return (
            "Debug systematically: reproduce the problem with the smallest input, "
            "write down the expected and actual result, inspect the first failing "
            "line, and test one change at a time. Check empty, boundary, and invalid "
            "inputs before assuming the algorithm is wrong.\n\n"
            "Try this check: what is the smallest input that still fails?"
        )

    language_names = (
        "python", "java", "c", "c++", "javascript", "typescript", "go",
        "rust", "sql", "kotlin", "swift", "c#",
    )
    detected_language = next((name for name in language_names if name in text), None)
    topic = subject or detected_language or "this programming topic"
    return (
        f"Let's break down {topic}. I could not identify one exact concept yet. "
        "Share the code or example, the expected result, and what actually "
        "happened. Start by testing the smallest valid input and one boundary "
        "case; that usually reveals the missing assumption."
    )


def _format_answer(answer: str) -> str:
    return (
        f"{answer}\n\n"
        "Try this check: explain the rule in your own words and test it with "
        "one normal case and one edge case."
    )
