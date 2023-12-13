# AutoPy: An Automated Test-Case Generation Engine for Python

## Author[s]: 
Eesha Agarwal for COS 516 (Fall 2023)
Under the guidance and mentorship of Professor Aarti Gupta and Mike He
Princeton University Department of Computer Science

## Description
AutoPy is a constrained automated test-case generation engine for Python. Provided with a function with any number of inputs, AutoPy analyses the different execution paths in the program. The key goals for each path are to 1) generate a set of specific input values which lead to the execution of the given path, 2) check for the possibility of a variety of different errors along the path including assertion violations, uncaught exceptions, and security vulnerabilities, or 3) declare a path to be unsatisfiable, and the corresponding code to be dead/unreachable. Currently, the engine works to automatically generate test cases, check for assertion violations, and identify dead code for a subset of the Python programming language, focusing specifically on support for primitive numerical data types, control flow and nested conditionals, and assertions. Support for loops and detection of non-terminating iterables, more complex data structures, and the usage of external libraries and the integration and composition of functions is excluded.

## Directory Structure
`autopy_test_gen.py` contains the logic and code for the test-case generation engine, including the parsing of the Python source code, the extraction of conditional branches, assertions, and relevant conditions, the actual solving of the constraints, and the generation of test-cases, detection of dead branches, and identification of failing assertions.
`manual-tests` is a directory that contains 5 hand-crafted examples that meticulously test the multiple capabities of AutoPy simultaneously.
`gpt-tests` is a directory that contains automatically-generated test cases to test this automated test-case generation engine. The tests are simpler, focus on specific capabilities of the engine, and are generated using the prompt in `gpt-tests/gpt-prompt.txt`.
`cos516_final_report` is a detailed report on the project, including details of implementation, capabilities, results, evaluation, and
potential ideas for future work.

## How It Works
- **AST Parsing**: The application reads a Python source file, parses it into an AST, and extracts conditional branches.
- **Symbolic Execution**: Each branch is symbolically executed using Z3 to check for satisfiability and generate test cases.
- **Dead Code Identification**: It identifies parts of the code that are never executed (dead code) and provides insights about these sections.
- **Test Case Generation**: For each valid branch, the application generates a set of input values that can be used for testing.

## How to Use
The only external dependency for this project is the `z3-solver` for Python. Once this is installed, AutoPy may be run on any single-function-containing Python program by running:

`python3 autopy_test_gen.py < testfile.txt`

where testfile.txt is a text file containing the Python program to be analyzed.

## Output
- The application prints out each branch with its conditions.
- Indicates whether a branch is satisfiable or represents dead code.
- For satisfiable branches, it provides test cases.
- Highlights unreachable code segments and their locations in the source file.
