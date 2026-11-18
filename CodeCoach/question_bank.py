from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

try:
    import requests
except Exception:
    requests = None

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)
CACHE = DATA_DIR / "a2z_catalog.json"
REMOTE = "https://raw.githubusercontent.com/septilex/a2z-tracker/main/dsa_tracker/a2z_problems_simple.json"

# A bundled seed made only from titles known to occur in the current sheet.
# The full 474-title catalog is fetched once and cached when internet is available.
SEED = [
("Input Output","Learn the basics","Easy"),("Cpp Basics","Learn the basics","Easy"),("If ElseIf","Learn the basics","Easy"),("Switch Case","Learn the basics","Easy"),("What are arrays, strings?","Learn the basics","Easy"),("For loops","Learn the basics","Easy"),("While loops","Learn the basics","Easy"),("Functions (Pass by Reference and Value)","Learn the basics","Easy"),("Theory with examples","Learn the basics","Easy"),("Easy and Medium","Learn the basics","Easy"),("Hard","Learn the basics","Easy"),("Pattern 1","Learn the basics","Easy"),("Pattern 2","Learn the basics","Easy"),("Pattern 3","Learn the basics","Easy"),("Pattern 4","Learn the basics","Easy"),("Pattern 5","Learn the basics","Easy"),("Pattern 6","Learn the basics","Easy"),("Pattern 7","Learn the basics","Easy"),("Pattern 8","Learn the basics","Easy"),("Pattern 9","Learn the basics","Easy"),("Pattern 10","Learn the basics","Easy"),("Pattern 11","Learn the basics","Easy"),("Pattern 12","Learn the basics","Easy"),("Pattern 13","Learn the basics","Easy"),("Pattern 14","Learn the basics","Easy"),("Pattern 15","Learn the basics","Easy"),("Pattern 16","Learn the basics","Easy"),("Pattern 17","Learn the basics","Easy"),("Pattern 18","Learn the basics","Easy"),("Pattern 19","Learn the basics","Easy"),("Pattern 20","Learn the basics","Medium"),("Pattern 21","Learn the basics","Medium"),("Pattern 22","Learn the basics","Medium"),("STL","Learn the basics","Easy"),("Java Collections","Learn the basics","Easy"),("Count all Digits of a Number","Learn the basics","Easy"),("Reverse a number","Learn the basics","Easy"),("Palindrome Number","Learn the basics","Easy"),("GCD of Two Numbers","Learn the basics","Easy"),("Check if the Number is Armstrong","Learn the basics","Easy"),("Print all Divisors","Learn the basics","Easy"),("Check for Prime Number","Learn the basics","Easy"),("Understand recursion by print something N times","Learn the basics","Easy"),("Print name N times using recursion","Learn the basics","Easy"),("Print 1 to N using Recursion","Learn the basics","Easy"),("Print N to 1 using Recursion","Learn the basics","Easy"),("Sum of First N Numbers","Learn the basics","Easy"),("Factorial of a given number","Learn the basics","Easy"),("Reverse an array","Learn the basics","Easy"),("Check if String is Palindrome or Not","Learn the basics","Easy"),("Fibonacci Number","Learn the basics","Easy"),("Basic Hashing","Learn the basics","Easy"),("Counting Frequencies of Array Elements","Learn the basics","Easy"),("Highest Occurring Element in an Array","Learn the basics","Easy"),
("Selection Sort","Learn Important Sorting Techniques","Easy"),("Bubble Sort","Learn Important Sorting Techniques","Easy"),("Insertion Sorting","Learn Important Sorting Techniques","Easy"),("Merge Sorting","Learn Important Sorting Techniques","Medium"),("Recursive Bubble Sort","Learn Important Sorting Techniques","Easy"),("Recursive Insertion Sort","Learn Important Sorting Techniques","Easy"),("Quick Sorting","Learn Important Sorting Techniques","Easy"),
("Largest Element","Arrays","Easy"),("Second Largest Element","Arrays","Easy"),("Check if the Array is Sorted II","Arrays","Easy"),("Remove duplicates from Sorted array","Arrays","Easy"),("Left Rotate Array by One","Arrays","Easy"),("Left Rotate Array by K Places","Arrays","Easy"),("Move Zeros to End","Arrays","Easy"),("Linear Search","Arrays","Easy"),("Union of two sorted arrays","Arrays","Easy"),("Find missing number","Arrays","Easy"),("Maximum Consecutive Ones","Arrays","Easy"),("Find the number that appears once, and other numbers twice.","Arrays","Medium"),("Longest subarray with given sum K(positives)","Arrays","Medium"),("Longest subarray with sum K","Arrays","Medium"),("Two Sum","Arrays","Easy"),("Sort an array of 0's 1's and 2's","Arrays","Medium"),("Majority Element-I","Arrays","Easy"),("Kadane's Algorithm","Arrays","Medium"),("Print subarray with maximum subarray sum (extended version of above problem)","Arrays","Medium"),("Stock Buy and Sell","Arrays","Medium"),("Rearrange array elements by sign","Arrays","Medium"),("Next Permutation","Arrays","Medium"),("Leaders in an Array","Arrays","Medium"),("Longest Consecutive Sequence in an Array","Arrays","Medium"),("Set Matrix Zeroes","Arrays","Medium"),("Rotate matrix by 90 degrees","Arrays","Medium"),("Print the matrix in spiral manner","Arrays","Medium"),("Count subarrays with given sum","Arrays","Medium"),("Pascal's Triangle I","Arrays","Easy"),("Majority Element-II","Arrays","Hard"),("3 Sum","Arrays","Medium"),("4 Sum","Arrays","Medium"),("Largest Subarray with Sum 0","Arrays","Medium"),("Count subarrays with given xor K","Arrays","Hard"),("Merge Overlapping Subintervals","Arrays","Medium"),("Merge two sorted arrays without extra space","Arrays","Medium"),("Find the repeating and missing number","Arrays","Hard"),("Count Inversions","Arrays","Hard"),
]

# Extra well-known titles from the same current A2Z track; used as offline seeds.
EXTRA = [
("Find the first and last occurrence of a given element in a sorted array","Binary Search","Easy"),("Count occurrences of a number in a sorted array with duplicates","Binary Search","Easy"),("Search in Rotated Sorted Array I","Binary Search","Medium"),("Search in Rotated Sorted Array II","Binary Search","Medium"),("Find minimum in Rotated Sorted Array","Binary Search","Medium"),("Find out how many times the array has been rotated","Binary Search","Medium"),("Single Element in a Sorted Array","Binary Search","Medium"),("Find peak element","Binary Search","Medium"),("Square Root of a number","Binary Search","Easy"),("Nth Root of a Number","Binary Search","Easy"),("Koko Eating Bananas","Binary Search","Medium"),("Minimum days to make M bouquets","Binary Search","Medium"),("Capacity to Ship Packages within D Days","Binary Search","Medium"),("Aggressive Cows","Binary Search","Hard"),("Book Allocation Problem","Binary Search","Hard"),("Painter's Partition Problem","Binary Search","Hard"),("Median of two sorted arrays","Binary Search","Hard"),
("Reverse Words in a String","Strings","Medium"),("Longest Palindromic Substring","Strings","Medium"),("Remove outermost Paranthesis","Strings","Easy"),("Reverse Every Word in a String","Strings","Easy"),("Largest odd number in a string","Strings","Easy"),("Longest Common Prefix","Strings","Easy"),("Isomorphic Strings","Strings","Easy"),("Check if two strings are anagrams","Strings","Easy"),("Sort Characters by Frequency","Strings","Medium"),("Maximum Nesting Depth of Parentheses","Strings","Easy"),("Roman Number to Integer and vice-versa","Strings","Easy"),("Implement Atoi","Strings","Medium"),
("Reverse a LinkedList","Linked List","Easy"),("Find the middle of a LinkedList","Linked List","Easy"),("Detect a cycle in Linked List","Linked List","Easy"),("Find the length of the loop in linked list","Linked List","Medium"),("Check if LL is palindrome or not","Linked List","Easy"),("Segregate odd and even nodes in LinkedList","Linked List","Medium"),("Remove Nth node from the back of the LinkedList","Linked List","Medium"),("Delete the middle node of the LinkedList","Linked List","Medium"),("Sort a Linked List","Linked List","Medium"),("Intersection of Two Linked Lists","Linked List","Easy"),("Add two numbers represented as LinkedLists","Linked List","Medium"),("Rotate a LinkedList","Linked List","Medium"),("Reverse Linked List in groups of Size K","Linked List","Hard"),("Flattening of a Linked List","Linked List","Hard"),
("Subset Sums","Recursion","Medium"),("Subset Sum","Recursion","Medium"),("Combination Sum","Recursion","Medium"),("Combination Sum II","Recursion","Medium"),("Palindrome Partitioning","Recursion","Hard"),("K-th permutation sequence","Recursion","Hard"),("Print all permutations of a string/array","Recursion","Medium"),("N-Queens","Recursion","Hard"),("Rat in a Maze","Recursion","Hard"),("Word Search","Recursion","Medium"),
("Check if the i-th bit is set or not","Bit Manipulation","Easy"),("Check if a number is odd or even","Bit Manipulation","Easy"),("Power Set","Bit Manipulation","Medium"),("Divide two integers without using multiplication, division and mod operator","Bit Manipulation","Medium"),("Count number of set bits","Bit Manipulation","Easy"),("Minimum bit flips to convert number","Bit Manipulation","Easy"),
("Implement Stack using Arrays","Stack & Queues","Easy"),("Implement Queue using Arrays","Stack & Queues","Easy"),("Implement Stack using Queue","Stack & Queues","Easy"),("Implement Queue using Stack","Stack & Queues","Easy"),("Valid Parentheses","Stack & Queues","Easy"),("Next Greater Element","Stack & Queues","Medium"),("Next Greater Element II","Stack & Queues","Medium"),("Largest Rectangle in Histogram","Stack & Queues","Hard"),("Trapping Rainwater","Stack & Queues","Hard"),("Stock Span Problem","Stack & Queues","Medium"),
("Longest Substring Without Repeating Characters","Sliding Window","Medium"),("Max Consecutive Ones III","Sliding Window","Medium"),("Fruit Into Baskets","Sliding Window","Medium"),("Longest Repeating Character Replacement","Sliding Window","Medium"),("Binary subarray with sum","Sliding Window","Medium"),("Count number of nice subarrays","Sliding Window","Medium"),("Number of Substrings Containing All Three Characters","Sliding Window","Medium"),("Minimum Window Substring","Sliding Window","Hard"),
("Kth largest element in an array","Heaps","Medium"),("Kth smallest element in an array","Heaps","Medium"),("Merge K sorted arrays","Heaps","Hard"),("Find median from Data Stream","Heaps","Hard"),("Top K Frequent Elements","Heaps","Medium"),("Replace elements by their rank in the array","Heaps","Medium"),
("Assign Cookies","Greedy","Easy"),("Fractional Knapsack","Greedy","Medium"),("Minimum Coins","Greedy","Easy"),("Lemonade Change","Greedy","Easy"),("Valid Parenthesis String","Greedy","Medium"),("N meetings in one room","Greedy","Easy"),("Jump Game","Greedy","Medium"),("Jump Game 2","Greedy","Medium"),("Candy","Greedy","Hard"),
("Preorder Traversal","Binary Trees","Easy"),("Inorder Traversal","Binary Trees","Easy"),("Postorder Traversal","Binary Trees","Easy"),("Level Order Traversal","Binary Trees","Medium"),("Maximum Depth of Binary Tree","Binary Trees","Easy"),("Check for Balanced Binary Tree","Binary Trees","Easy"),("Diameter of Binary Tree","Binary Trees","Easy"),("Maximum Path Sum","Binary Trees","Hard"),("Same Tree","Binary Trees","Easy"),("Zig Zag Traversal","Binary Trees","Medium"),("Boundary Traversal","Binary Trees","Medium"),("Vertical Order Traversal","Binary Trees","Hard"),("Top View of Binary Tree","Binary Trees","Medium"),("Bottom View of Binary Tree","Binary Trees","Medium"),("Left/Right View of Binary Tree","Binary Trees","Medium"),("Symmetric Binary Tree","Binary Trees","Easy"),("Flatten Binary Tree to Linked List","Binary Trees","Medium"),
("Search in a Binary Search Tree","BST","Easy"),("Find Min/Max in BST","BST","Easy"),("Ceil in a Binary Search Tree","BST","Medium"),("Floor in a Binary Search Tree","BST","Medium"),("Insert a given Node in Binary Search Tree","BST","Medium"),("Delete a Node in BST","BST","Medium"),("Kth Smallest Element in a BST","BST","Medium"),("Validate BST","BST","Medium"),("Lowest Common Ancestor in a BST","BST","Medium"),("Two Sum in BST","BST","Medium"),
("Graph Representation","Graphs","Easy"),("BFS","Graphs","Easy"),("DFS","Graphs","Easy"),("Number of Provinces","Graphs","Medium"),("Number of Islands","Graphs","Medium"),("Flood Fill","Graphs","Easy"),("Rotten Oranges","Graphs","Medium"),("Detect Cycle in Undirected Graph","Graphs","Medium"),("Detect Cycle in Directed Graph","Graphs","Medium"),("Topological Sort","Graphs","Medium"),("Course Schedule","Graphs","Medium"),("Dijkstra's Algorithm","Graphs","Medium"),("Bellman-Ford Algorithm","Graphs","Medium"),("Floyd Warshall Algorithm","Graphs","Medium"),("Minimum Spanning Tree","Graphs","Medium"),("Kruskal's Algorithm","Graphs","Medium"),("Prim's Algorithm","Graphs","Medium"),("Bridges in Graph","Graphs","Hard"),("Articulation Point","Graphs","Hard"),("Word Ladder","Graphs","Hard"),
("Fibonacci","Dynamic Programming","Easy"),("Climbing Stairs","Dynamic Programming","Easy"),("House Robber","Dynamic Programming","Medium"),("Maximum sum of non-adjacent elements","Dynamic Programming","Medium"),("Ninja's Training","Dynamic Programming","Medium"),("Grid Unique Paths","Dynamic Programming","Medium"),("Minimum Path Sum","Dynamic Programming","Medium"),("Triangle","Dynamic Programming","Medium"),("Partition Equal Subset Sum","Dynamic Programming","Medium"),("0/1 Knapsack","Dynamic Programming","Medium"),("Coin Change","Dynamic Programming","Medium"),("Target Sum","Dynamic Programming","Medium"),("Longest Common Subsequence","Dynamic Programming","Medium"),("Longest Palindromic Subsequence","Dynamic Programming","Medium"),("Edit Distance","Dynamic Programming","Hard"),("Distinct Subsequences","Dynamic Programming","Hard"),("Best Time to Buy and Sell Stock II","Dynamic Programming","Medium"),("Best Time to Buy and Sell Stock III","Dynamic Programming","Hard"),("Best Time to Buy and Sell Stock IV","Dynamic Programming","Hard"),("Longest Increasing Subsequence","Dynamic Programming","Medium"),("Matrix Chain Multiplication","Dynamic Programming","Hard"),("Burst Balloons","Dynamic Programming","Hard"),
("Implement Trie I","Tries","Medium"),("Implement Trie II","Tries","Medium"),("Longest Word with All Prefixes","Tries","Medium"),("Number of Distinct Substrings","Tries","Hard"),("Maximum XOR of Two Numbers in an Array","Tries","Hard"),
("Z-Function","Strings Advanced","Hard"),("KMP Algorithm","Strings Advanced","Hard"),("Rabin Karp","Strings Advanced","Hard"),("Minimum characters needed to make a string palindrome","Strings Advanced","Hard"),
]


def _normalize(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out=[]
    seen=set()
    for i, item in enumerate(items,1):
        name=str(item.get("problem_name","")).strip()
        if not name: continue
        key=(name.lower(),str(item.get("topic","")).lower())
        if key in seen: continue
        seen.add(key)
        out.append({
            "id": int(item.get("id",i)),
            "problem_name": name,
            "topic": str(item.get("topic","General")),
            "difficulty": str(item.get("difficulty","Medium")),
            "leetcode_url": str(item.get("leetcode_url", "")),
            "youtube_url": str(item.get("youtube_url", "")),
        })
    return out


def load_bank(force_refresh: bool=False) -> tuple[list[dict[str,Any]], str]:
    if not force_refresh and CACHE.exists():
        try:
            data=json.loads(CACHE.read_text(encoding="utf-8"))
            if isinstance(data,list) and len(data)>=400:
                return _normalize(data), "cached-full"
        except Exception:
            pass
    if requests is not None:
        try:
            r=requests.get(REMOTE,timeout=8)
            r.raise_for_status()
            data=r.json()
            if isinstance(data,list) and len(data)>=400:
                CACHE.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
                return _normalize(data), "downloaded-full"
        except Exception:
            pass
    seed=[{"id":i,"problem_name":n,"topic":t,"difficulty":d,"leetcode_url":"","youtube_url":""} for i,(n,t,d) in enumerate(SEED+EXTRA,1)]
    return _normalize(seed), "bundled-seed"


def topic_alias(topic: str) -> str:
    x = re.sub(r"[^a-z0-9+# ]+", " ", topic.lower()).strip()
    x = re.sub(r"\s+", " ", x)
    aliases = {
        "array": "arrays", "arrays": "arrays",
        "string": "strings", "strings": "strings",
        "linked": "linkedlist", "linked list": "linkedlist",
        "linked lists": "linkedlist", "linkedlist": "linkedlist",
        "recursion": "recursion", "backtracking": "recursion",
        "binary search": "binary search", "search": "binary search",
        "stack": "stack & queues", "queue": "stack & queues",
        "stacks": "stack & queues", "queues": "stack & queues",
        "heap": "heaps", "heaps": "heaps",
        "greedy": "greedy",
        "tree": "binary trees", "trees": "binary trees",
        "binary tree": "binary trees", "binary trees": "binary trees",
        "bst": "bst", "binary search tree": "bst",
        "graph": "graphs", "graphs": "graphs",
        "dp": "dynamic programming", "dynamic programming": "dynamic programming",
        "trie": "tries", "tries": "tries",
        "bit": "bit manipulation", "bit manipulation": "bit manipulation",
        "sorting": "sorting", "sort": "sorting",
        "sliding window": "sliding window",
        "two pointer": "sliding window", "two pointers": "sliding window",
    }
    return aliases.get(x, x)


def choose_problem(bank, topic=None, difficulty=None, exclude=None):
    exclude = {x.lower() for x in (exclude or [])}
    candidates = list(bank)

    if topic:
        wanted = topic_alias(topic)
        wanted_key = re.sub(r"[^a-z0-9]+", "", wanted)

        filtered = []
        for q in candidates:
            qt = topic_alias(q.get("topic", ""))
            qt_key = re.sub(r"[^a-z0-9]+", "", qt)
            if wanted_key in qt_key or qt_key in wanted_key:
                filtered.append(q)

        # Explicit topic requests must not fall back to an unrelated topic.
        if not filtered:
            return None
        candidates = filtered

    if difficulty:
        filtered = [
            q for q in candidates
            if q.get("difficulty", "").lower() == difficulty.lower()
        ]
        if filtered:
            candidates = filtered
        elif topic:
            return None

    fresh = [
        q for q in candidates
        if q.get("problem_name", "").lower() not in exclude
    ]
    if fresh:
        candidates = fresh

    import random
    return random.choice(candidates) if candidates else None



def infer_topic(text: str):
    low = re.sub(r"[^a-z0-9+# ]+", " ", text.lower())
    low = re.sub(r"\s+", " ", low).strip()

    checks = [
        ("binary search tree", "bst"),
        ("dynamic programming", "dynamic programming"),
        ("binary search", "binary search"),
        ("linked list", "linkedlist"),
        ("linkedlist", "linkedlist"),
        ("binary tree", "binary trees"),
        ("stack", "stack & queues"),
        ("queue", "stack & queues"),
        ("graph", "graphs"),
        ("recursion", "recursion"),
        ("backtracking", "recursion"),
        ("heap", "heaps"),
        ("greedy", "greedy"),
        ("trie", "tries"),
        ("bit manipulation", "bit manipulation"),
        ("sorting", "sorting"),
        ("array", "arrays"),
        ("string", "strings"),
    ]
    for key, canonical in checks:
        if key in low:
            return canonical
    return None



def infer_difficulty(text: str):
    low=text.lower()
    if "hard" in low or "difficult" in low: return "Hard"
    if "easy" in low or "simple" in low: return "Easy"
    if "medium" in low: return "Medium"
    return None


def problem_card(q: dict[str,Any]) -> str:
    n=q["problem_name"]
    t=q["topic"]
    d=q["difficulty"]
    # Original concise prompt; intentionally not copied from any source editorial/problem statement.
    return f"### 🧩 {n}\n\n**Topic:** {t}  \n**Difficulty:** {d}\n\nExplain your approach first. I’ll interview you through it instead of immediately giving you the solution."


def pattern_for(name: str, topic: str) -> str:
    s=(name+" "+topic).lower()
    patterns=[
      ("hash map / frequency map",["two sum","frequency","anagram","occurring","subarray with sum","xor"]),
      ("two pointers",["two sum","remove duplicates","rotate","palindrome","3 sum","4 sum","merge two sorted"]),
      ("sliding window",["longest substring","window","consecutive","subarrays","nice subarrays"]),
      ("binary search on answer",["koko","minimum days","capacity","aggressive cows","book allocation","painter"]),
      ("binary search",["search","occurrence","peak","sqrt","median","rotated","single element"]),
      ("monotonic stack",["next greater","largest rectangle","stock span","rainwater"]),
      ("BFS/DFS",["islands","flood fill","provinces","rotten","traversal","graph","cycle"]),
      ("dynamic programming",["dynamic programming","fibonacci","climbing","knapsack","subsequence","partition","coin","edit distance","matrix chain","burst"]),
      ("greedy",["greedy","activity","cookies","knapsack","candy","jump","meeting"]),
      ("backtracking",["permutation","subset","combination","n-queens","rat in a maze","word search","palindrome partition"]),
      ("tree recursion",["tree","bst","binary tree"]),
      ("heap / priority queue",["heap","kth","median","merge k","frequent"]),
      ("trie",["trie","prefix","xor"]),
      ("sorting / divide and conquer",["sort","inversion","merge","quick"]),
      ("bit manipulation",["bit","power set","set bits","xor"]),
    ]
    for p, words in patterns:
        if any(w in s for w in words): return p
    return "direct simulation / data structure"


def hints(q, level: int) -> list[str]:
    p=pattern_for(q["problem_name"],q["topic"])
    name=q["problem_name"]
    generic={
      "hash map / frequency map":[
        f"First ask what information from earlier elements would make the current element easier to process.",
        f"Try replacing repeated searching with a data structure that gives fast lookup.",
        f"For each current value, identify the complementary value or frequency you need and check whether it has already been seen.",
        f"Store the useful information as you scan once; be careful about whether you need the index, count, or boolean presence.",
        f"A HashMap/HashSet-based solution is likely the intended optimization. State exactly what the key and value represent before coding.",
        f"Now write the invariant: after processing index i, what does your map guarantee? That invariant should make the final lookup immediate.",
      ],
      "two pointers":[
        "Look for a way to move from both ends or maintain two indices instead of repeatedly rescanning the same range.",
        "Ask what condition tells you which pointer can safely move.",
        "Write down what each pointer represents and what part of the data is already settled.",
        "If the input is sorted, exploit that order; if not, consider whether sorting is allowed and what it changes about complexity.",
        "At every pointer move, make sure you never discard a candidate that could still be part of an answer.",
        "State the invariant for the current left/right window before writing code.",
      ],
      "sliding window":[
        "Instead of checking every substring/subarray independently, maintain one moving window.",
        "Ask what makes the current window valid or invalid.",
        "When the window becomes invalid, which boundary should move and what state must be updated?",
        "Track only the information needed to restore validity when the left boundary advances.",
        "Try to make each element enter and leave the window at most once.",
        "Your target complexity should usually be linear if each pointer moves monotonically.",
      ],
      "binary search":[
        "What property is monotonic? Binary search needs a yes/no decision that changes only once.",
        "Define the search space precisely: what are low and high representing?",
        "For the midpoint, decide whether the answer is on the left, on the right, or exactly at mid.",
        "Be careful with duplicates and with the loop condition so the search space always shrinks.",
        "Write the predicate before writing the binary-search loop.",
        "Test boundary cases: one element, answer at an endpoint, and no valid answer.",
      ],
      "binary search on answer":[
        "Instead of searching indices, search the possible value of the answer.",
        "Can you write a feasibility function: 'Is it possible with answer = X?'",
        "If feasibility is monotonic, use binary search over X.",
        "Find tight lower and upper bounds from the input rather than using arbitrary constants.",
        "The outer binary search is logarithmic; focus on making the feasibility check correct and efficient.",
        "Check whether the predicate changes from false to true or true to false exactly once.",
      ],
      "monotonic stack":[
        "For each element, ask whether you need the next greater/smaller unresolved element.",
        "A stack can keep candidates whose answer has not been found yet.",
        "When the current element resolves previous candidates, pop them and assign their answer.",
        "Choose increasing or decreasing stack order based on the relation you need.",
        "Each element should be pushed and popped at most once for an O(n) solution.",
        "Walk through a small example and label exactly what remains unresolved on the stack.",
      ],
      "BFS/DFS":[
        "Model the input as states/nodes and identify how one state reaches its neighbors.",
        "Ask whether you need shortest number of edges, reachability, or full exploration.",
        "BFS is natural for unweighted shortest paths; DFS is natural for exploration and recursive structure.",
        "Track visited states so you do not process the same state indefinitely.",
        "For grids, think in four/eight directions and mark a cell at the right time.",
        "State what your queue/stack contains at every step before coding.",
      ],
      "dynamic programming":[
        "Identify the smaller version of the same problem: what would the answer for a prefix, index, or smaller capacity mean?",
        "Write the state in one sentence before choosing an array/table.",
        "Find the transition: which previous states can produce the current state?",
        "Find the base cases independently of the transition.",
        "Check whether the state can be compressed to one or two previous rows/values.",
        "Only after the recurrence is clear should you choose memoization or tabulation.",
      ],
      "greedy":[
        "Look for a local choice that can be proven safe rather than trying every combination.",
        "Ask what ordering makes the best local decision visible.",
        "Try sorting by the quantity that controls the next decision.",
        "Explain why choosing the local best cannot hurt a future solution.",
        "Test the greedy choice against a small counterexample before trusting it.",
        "If you cannot justify the greedy choice, compare it with a DP state instead of guessing.",
      ],
      "backtracking":[
        "Build the answer one decision at a time and define what one recursive call represents.",
        "At each position, list the choices you can make.",
        "After trying a choice, undo its effect before trying the next choice.",
        "Prune a branch as soon as it cannot lead to a valid answer.",
        "Separate 'choose', 'recurse', and 'unchoose' clearly.",
        "Write the base case as 'one complete candidate has been constructed'.",
      ],
      "tree recursion":[
        "Ask what the answer for a node depends on from its left and right subtrees.",
        "Define exactly what your recursive function returns for one node.",
        "Handle the null node first; it is often the base case.",
        "Combine left and right results only after both recursive calls return.",
        "For path problems, distinguish a value that can be returned upward from a global best answer.",
        "Trace the recursion on a tree with only three nodes before coding.",
      ],
      "heap / priority queue":[
        "Ask whether you repeatedly need the smallest/largest remaining item.",
        "A heap can keep the next most important candidate at the top.",
        "For top-K problems, decide whether a min-heap or max-heap keeps the useful K items.",
        "If merging sorted streams, put the next item from each stream into a min-heap.",
        "Track the heap size invariant so memory does not grow unnecessarily.",
        "State the cost of each push/pop and multiply by the number of operations.",
      ],
      "trie":[
        "The problem is about prefixes or character-by-character branching; a trie may avoid repeated string comparisons.",
        "Think of each node as one prefix and each edge as one character.",
        "Decide what information must be stored at a node: terminal flag, count, or other metadata.",
        "Insertion and lookup follow the characters of a word one by one.",
        "For XOR-trie problems, each level represents a bit rather than a character.",
        "Estimate complexity in terms of word length or bit width, not only number of words.",
      ],
      "sorting / divide and conquer":[
        "Ask whether sorting exposes the order needed by the later logic.",
        "If you need an O(n log n) approach, consider divide-and-conquer sorting or a built-in sort plus a linear scan.",
        "For merge-based counting, think about what can be counted while merging two sorted halves.",
        "Keep the subproblem boundaries precise before writing recursion.",
        "Check whether extra arrays are allowed or whether an in-place approach is required.",
        "State the recurrence or sorting cost before claiming the complexity.",
      ],
      "bit manipulation":[
        "Write a small number in binary and inspect the relevant bit position.",
        "Remember that shifting can isolate or move a bit; masking can test it.",
        "XOR cancels equal bits and is useful when pairs appear twice.",
        "For powers of two, inspect the relationship between n and n-1 in binary.",
        "If the problem asks about all subsets, think of bit masks as subset selectors.",
        "Test the bit logic on zero, one, and a value with multiple set bits.",
      ],
      "direct simulation / data structure":[
        "Translate the statement into a small example before choosing a data structure.",
        "Ask which information must be available quickly at each step.",
        "Look for repeated work that can be stored instead of recomputed.",
        "Write the simplest correct brute-force idea first, then identify its bottleneck.",
        "Check edge cases before optimizing.",
        "State the invariant of your loop or data structure in one sentence.",
      ],
    }
    return generic.get(p,generic["direct simulation / data structure"])


def feedback_variants(q, quality: str) -> list[str]:
    name=q["problem_name"]
    if quality=="good":
        return [
          f"That is a strong direction for **{name}**. You identified the key structure. Now justify why it gives the required complexity.",
          "Good. The important part is not only the data structure but the invariant it maintains. Can you state that invariant?",
          "Yes — that approach is plausible. Walk me through one small example so we can verify the state changes.",
          "Nice reasoning. Before coding, tell me what happens on the smallest and largest meaningful edge cases.",
          "You're on the right track. Now see if you can reduce any repeated work in your current approach.",
        ]
    if quality=="partial":
        return [
          "You're close, but there is one missing piece. Focus on what information must be remembered between iterations.",
          "The core idea is promising. Let's test it on a case where the obvious choice fails.",
          "I see the direction. The part I'd revisit is the transition from one state to the next.",
          "Your approach can work for some cases. What happens when duplicates, boundaries, or an empty input appear?",
          "Before changing the whole approach, identify the exact operation that is making the solution too slow or incorrect.",
        ]
    return [
      "Let's slow down and isolate the first decision. What should the algorithm do for the smallest input?",
      "No problem. Start with the brute-force idea and tell me what makes it expensive.",
      "You're not expected to see the optimal solution immediately. Let's identify the repeated work first.",
      "Try describing the problem without code: what information do you need at each step?",
      "Let's take one tiny example and simulate it by hand. The pattern usually becomes clearer from there.",
    ]


def concise_solution(q) -> str:
    p=pattern_for(q["problem_name"],q["topic"])
    complexity={
      "hash map / frequency map":"Usually O(n) time and O(n) auxiliary space.",
      "two pointers":"Often O(n) after any required sorting; auxiliary space is commonly O(1) for in-place scans.",
      "sliding window":"Usually O(n) because each pointer moves forward at most n times.",
      "binary search":"O(log n) when the predicate/search space is valid and O(1) extra space for iterative code.",
      "binary search on answer":"O(log R × feasibility-check), where R is the answer range.",
      "monotonic stack":"Usually O(n) because each element is pushed and popped at most once.",
      "BFS/DFS":"Typically O(V+E) on graphs, or O(rows×cols) on a grid.",
      "dynamic programming":"Depends on state count and transition cost; commonly O(states × transitions) time and O(states) space.",
      "greedy":"Often O(n log n) when sorting is required, followed by a linear scan.",
      "backtracking":"Exponential in the worst case; pruning and constraints determine practical performance.",
      "tree recursion":"Usually O(n) when each node is processed a constant number of times.",
      "heap / priority queue":"Often O(n log k) or O(n log n), depending on whether the heap is bounded by k.",
      "trie":"Usually O(L) per operation where L is the key length.",
      "sorting / divide and conquer":"Usually O(n log n) for comparison sorting; exact space depends on the implementation.",
      "bit manipulation":"Often O(1) per fixed-width integer operation, or O(bits) when scanning bits.",
      "direct simulation / data structure":"Choose complexity from the exact operations required; first identify the dominant loop.",
    }
    return f"### 🧠 Solution direction\n\nFor **{q['problem_name']}**, the main pattern to investigate is **{p}**.\n\nA good solution should make the repeated work explicit, maintain a clear invariant, and handle edge cases before optimizing.\n\n**Complexity target:** {complexity.get(p,'Analyze the dominant operations from your final approach.')}\n\nIf you want, I can now give you a Java implementation and then walk through it line by line."
