"""Small, original practice bank for the hackathon demo.

The prompts are LeetCode-style but are written for Adhyan and are not copied
from any third-party problem set.
"""

QUESTIONS = [
    {
        "id": "py-two-sum-map",
        "subject": "Python",
        "topic": "Arrays and hash maps",
        "difficulty": "Easy",
        "prompt": "Given nums = [2, 7, 11, 15] and target = 9, which zero-based index pair should a one-pass hash-map solution return?",
        "options": ["[0, 1]", "[1, 2]", "[0, 3]", "[2, 3]"],
        "answer": 0,
        "explanation": "2 + 7 equals 9, and those values are at indices 0 and 1.",
    },
    {
        "id": "py-generator-memory",
        "subject": "Python",
        "topic": "Iterators",
        "difficulty": "Medium",
        "prompt": "Why is sum(x*x for x in range(10_000_000)) usually more memory-efficient than sum([x*x for x in range(10_000_000)])?",
        "options": [
            "The generator produces one value at a time",
            "Generators use multiple CPU cores",
            "Lists skip multiplication",
            "The generator changes integer precision",
        ],
        "answer": 0,
        "explanation": "A generator expression streams values instead of materializing the whole list.",
    },
    {
        "id": "py-mutable-default",
        "subject": "Python",
        "topic": "Functions and state",
        "difficulty": "Medium",
        "prompt": "What is the safest fix for def add(x, bucket=[]): bucket.append(x); return bucket?",
        "options": [
            "Use bucket=None and create [] inside the function",
            "Use a global list",
            "Convert x to a tuple",
            "Call the function twice before reading it",
        ],
        "answer": 0,
        "explanation": "Default objects are created once, so None lets each call create fresh state.",
    },
    {
        "id": "java-binary-search",
        "subject": "Java",
        "topic": "Binary search",
        "difficulty": "Easy",
        "prompt": "For a sorted array with inclusive left and right bounds, which midpoint avoids integer overflow?",
        "options": ["(left + right) / 2", "left + (right - left) / 2", "right - left / 2", "left * right / 2"],
        "answer": 1,
        "explanation": "Subtracting before adding avoids overflowing left + right.",
    },
    {
        "id": "java-equals-hashcode",
        "subject": "Java",
        "topic": "Collections",
        "difficulty": "Medium",
        "prompt": "If a Java class overrides equals, what must it also normally override for reliable HashMap key behavior?",
        "options": ["toString", "clone", "hashCode", "finalize"],
        "answer": 2,
        "explanation": "Equal objects must produce the same hash code for hash-based collections.",
    },
    {
        "id": "java-concurrent-map",
        "subject": "Java",
        "topic": "Concurrency",
        "difficulty": "Hard",
        "prompt": "Which structure is designed for concurrent key-value updates without synchronizing every caller?",
        "options": ["HashMap", "TreeMap", "ConcurrentHashMap", "ArrayDeque"],
        "answer": 2,
        "explanation": "ConcurrentHashMap provides thread-safe concurrent access with fine-grained coordination.",
    },
    {
        "id": "c-pointer-lifetime",
        "subject": "C Programming",
        "topic": "Memory safety",
        "difficulty": "Medium",
        "prompt": "What is wrong with returning a pointer to a local int buffer declared inside a C function?",
        "options": [
            "The pointer is always read-only",
            "The local storage lifetime ends when the function returns",
            "Pointers cannot refer to arrays",
            "The compiler converts it to Java",
        ],
        "answer": 1,
        "explanation": "The pointer becomes dangling after the function's stack frame is gone.",
    },
    {
        "id": "c-sizeof-array",
        "subject": "C Programming",
        "topic": "Arrays and pointers",
        "difficulty": "Easy",
        "prompt": "Inside void f(int values[]), what does sizeof(values) measure?",
        "options": ["The number of array elements", "The size of a pointer", "The size of one int", "Always zero"],
        "answer": 1,
        "explanation": "Array parameters are adjusted to pointers, so sizeof measures the pointer.",
    },
    {
        "id": "c-use-after-free",
        "subject": "C Programming",
        "topic": "Dynamic memory",
        "difficulty": "Hard",
        "prompt": "After free(ptr), which action is required before a later cleanup path might free it again?",
        "options": ["Set ptr = NULL", "Increment ptr", "Cast ptr to float", "Call sizeof(ptr)"],
        "answer": 0,
        "explanation": "Nulling the pointer makes the ownership state explicit and free(NULL) is safe.",
    },
    {
        "id": "algo-dijkstra",
        "subject": "Algorithms",
        "topic": "Graphs",
        "difficulty": "Medium",
        "prompt": "Dijkstra's algorithm is correct under which edge-weight condition?",
        "options": ["All weights are negative", "All weights are non-negative", "The graph is always a tree", "Every edge has weight one"],
        "answer": 1,
        "explanation": "Non-negative weights preserve the invariant that the smallest unsettled distance is final.",
    },
    {
        "id": "algo-sliding-window",
        "subject": "Algorithms",
        "topic": "Sliding window",
        "difficulty": "Medium",
        "prompt": "For the longest substring without repeated characters, what does a left pointer do when a duplicate appears?",
        "options": [
            "Moves backward to zero",
            "Moves past the previous occurrence",
            "Sorts the substring",
            "Deletes the entire string",
        ],
        "answer": 1,
        "explanation": "The window's left edge advances beyond the duplicate's prior index.",
    },
]


def public_question(question: dict) -> dict:
    return {
        key: value
        for key, value in question.items()
        if key not in {"answer", "explanation"}
    }


def get_question(question_id: str) -> dict | None:
    return next((item for item in QUESTIONS if item["id"] == question_id), None)
