import ast
from z3 import *
import random

class If_Node():
    def __init__(self, condition, assertion = False):
        self.condition = condition
        self.assertion = assertion
        self.if_branch = None
        self.else_branch = None
    
    def add_branch(self, condition, if_branch = True, assertion = False):
        child_node = If_Node(condition, assertion)
        
        if if_branch:
            self.if_branch = child_node
            
        else:
            self.else_branch = child_node

    def get_all_branches(self, path=[], branches=[]):
        if self is None:
            return

        if self.condition:
            path.append([self.condition, self.assertion])

        if self.if_branch is None and self.else_branch is None:
            branches.append(path)

        else:
            if self.if_branch is not None:
                self.if_branch.get_all_branches(path.copy(), branches)
            if self.else_branch is not None:
                self.else_branch.get_all_branches(path.copy(), branches)

        return branches

    def print_all_branches(self, path=[], branches=[]):
        if self is None:
            return branches if branches is not None else []

        if self.condition:
            condition_str = ast.unparse(self.condition) if isinstance(self.condition, ast.AST) else str(self.condition)
            path.append([condition_str, self.assertion])

        if self.if_branch is None and self.else_branch is None:
            branches.append(path)
        else:
            if self.if_branch is not None:
                self.if_branch.print_all_branches(path.copy(), branches)
            if self.else_branch is not None:
                self.else_branch.print_all_branches(path.copy(), branches)

        return branches
        
class ConditionExtractor(ast.NodeVisitor):
    def __init__(self):
        self.variables = []
        self.root = If_Node(None)
        self.line_nums = {}
        self.current_node = self.root
        self.assertions = []

    def visit_Assert(self, node):
        self.assertions.append(node.test)
        
    def visit_FunctionDef(self, node):
        for arg in node.args.args:
            self.variables.append(arg.arg)
        for n in node.body:
            self.generic_visit(n)
            if isinstance(n, ast.If):
                self.handle_if(n, self.current_node)

    def handle_if(self, node, curr, assertion = False, nodes = None):
        if not assertion:
            curr.add_branch(node.test)

            if node.orelse:
                self.line_nums[ast.unparse(node.test)] = (node.lineno, node.orelse[0].lineno - 2)
            else:
                self.line_nums[ast.unparse(node.test)] = (node.lineno, node.body[0].end_lineno)
            for n in node.body:
                if isinstance(n, ast.If):
                    self.handle_if(n, curr.if_branch)
                    break
                elif isinstance(n, ast.Assert):
                    self.handle_if(n, curr.if_branch, True, nodes = node.body[1:])
                    break
                else:
                    self.generic_visit(n)
                
            if node.orelse:
                curr.add_branch(ast.UnaryOp(op=ast.Not(), operand=node.test), False)
                for n in node.orelse:
                    if isinstance(n, ast.If):
                        self.handle_if(n, curr.else_branch)
                        break
                    elif isinstance(n, ast.Assert):
                        self.handle_if(n, curr.else_branch, True, nodes = node.orelse[1:])
                        break
                    else:
                        self.generic_visit(n)
                        
        else:
            curr.add_branch(node.test, assertion=True)

            if nodes is not None:
                if any(isinstance(next_node, ast.If) for next_node in nodes):
                    for i, n in enumerate(nodes):
                        if isinstance(n, ast.If):
                            self.handle_if(n, curr.if_branch, False, nodes = nodes[i+1:])
                        elif isinstance(n, ast.Assert):
                            self.handle_if(n, curr.if_branch, True, nodes = nodes[i+1:])
            else:
                self.generic_visit(node)

def convert_ast_to_z3(node, z3_vars):
    if isinstance(node, ast.UnaryOp):
        operand = convert_ast_to_z3(node.operand, z3_vars)
        if isinstance(node.op, ast.Not):
            return Not(operand)

    elif isinstance(node, ast.Compare):
        left = convert_ast_to_z3(node.left, z3_vars)
        right = convert_ast_to_z3(node.comparators[0], z3_vars)
        
        if isinstance(node.ops[0], ast.Gt):
            return left > right
        elif isinstance(node.ops[0], ast.Lt):
            return left < right
        elif isinstance(node.ops[0], ast.Eq):
            return left == right
        elif isinstance(node.ops[0], ast.NotEq):
            return left != right
        elif isinstance(node.ops[0], ast.GtE):
            return left >= right
        elif isinstance(node.ops[0], ast.LtE):
            return left <= right

        elif isinstance(node.ops[0], ast.And):
            return And(left, right)
        elif isinstance(node.ops[0], ast.Or):
            return Or(left, right)
        elif isinstance(node.ops[0], ast.Not):
            return Not(left, right)

    elif isinstance(node, ast.BoolOp):
        left = convert_ast_to_z3(node.values[0], z3_vars)
        right = convert_ast_to_z3(node.values[1], z3_vars)
        if isinstance(node.op, ast.And):
            return And(left, right)
        elif isinstance(node.op, ast.Or):
            return Or(left, right)
    
    elif isinstance(node, ast.Name):
        return z3_vars[node.id]
    elif isinstance(node, ast.Num):
        if isinstance(node.n, int):
            return IntVal(node.n)
        elif isinstance(node.n, float):
            return RealVal(node.n)
    elif isinstance(node, ast.Constant):
        return node.value
    
    raise NotImplementedError(f"AST node type {type(node)} not handled")

def generate_test_cases(variables, branches, assertions, rand_min=0, rand_max=100):
    all_cases = []
    branch_info = []
    conditions = []
    for i, branch in enumerate(branches):
        # collect assertions for this branch
        asserts = []
        solver = Solver()
        z3_vars = {var: Int(var) for var in variables}
        test_cases = {var: [] for var in variables}

        for condition in branch:
            if not condition[1]:
                z3_cond = (convert_ast_to_z3(condition[0], z3_vars))
                solver.add(z3_cond)

                # check if given condition made the branch unsatisfiable
                if solver.check() != sat:
                    branch_info.append((i, "UNSAT"))
                    for var in variables:
                        test_cases[var] = "UNSAT"
                    conditions.append(ast.unparse(condition[0]))
                    break
            else:
                asserts.append(condition[0])
            
        if solver.check() == sat:
            for assertion in asserts:
                z3_cond = (convert_ast_to_z3(assertion, z3_vars))
                solver.add(z3_cond)
                if solver.check != sat:
                    branch_info.append((i, f"UNSAT with assertion {ast.unparse(assertion)}"))
                    for var in variables:
                        test_cases[var] = "UNSAT"
                    conditions.append(ast.unparse(assertion))
                    break
            if solver.check() == sat:
                branch_info.append((i, "SAT"))
                model = solver.model()
                for var in variables:
                    z3_var = z3_vars[var]
                    if z3_var in model:
                        test_cases[var] = model[z3_var].as_long()
                    else:
                        test_cases[var] = random.randint(rand_min, rand_max)
                conditions.append("SAT")
        all_cases.append(test_cases)

    return all_cases, branch_info, conditions

def get_test_cases(source):
    parsed_ast = ast.parse(source)
    extractor = ConditionExtractor()
    extractor.visit(parsed_ast)
    string_branches = (extractor.root).print_all_branches()
    branches = (extractor.root).get_all_branches()

    test_cases, dead_code_branches, dead_code_conditions = generate_test_cases(extractor.variables, branches, extractor.assertions)
    return [string_branches, test_cases, dead_code_branches, dead_code_conditions, extractor.line_nums]

def __main__():
    source_code = sys.stdin.read()
    branches, test_cases, branch_info, dead_code_conditions, line_nums = get_test_cases(source_code)

    print("Number of branches:", len(branches))
    for i, branch_status in branch_info:
        print("Branch number:", i + 1)
        print("Branch conditions:", [(condition[0]) for condition in branches[i]])
        print("Branch status:", branch_status)
        if branch_status == "UNSAT":
            print("Status: Dead Code (UNSAT)")
            print(f"The condition that caused the dead code: {dead_code_conditions[i]}. Lines {line_nums[dead_code_conditions[i]][0]} - {line_nums[dead_code_conditions[i]][1]} are unreachable.")
        elif branch_status == "SAT":
            print("Test values:", test_cases[i])
        else:
            print("Status:", branch_status)
        print()

if __name__ == "__main__":
    __main__()