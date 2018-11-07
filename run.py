#! /usr/bin/python -u
import copy
import sys
import os
import re
import sys


identifier = r"[^\d\W]\w*"
space = r"[ \t]"
reference = fr"{{{space}*(?P<name>{identifier}){space}*}}"
value = r".+"
value_group = fr"{space}*(?P<value>.+?\S){space}*"
variable = fr"(?P<name>{identifier}){space}*={value_group}"
indented_line = fr"{space}+{value}{space}*\n"
indented_line_group = fr"{space}+{value_group}\n"
target = fr"^(?P<name>{identifier}):{space}*(?P<dependencies>(?:{identifier}{space}*)*)\n(?P<body>(?:{indented_line})*)"
comment = fr"^{space}*#{value}"
global_variable = fr"^{variable}$"
docstring = fr"^{space}*(?P<quote>[\"']){value_group}(?P=quote)"
"""
identifier a valid python identifier
reference = { identifier }
value = [reference | text]+
variable -> identifier = value
target = identifier: [identifier]+\n
    [value\n]*
"""


def parse(all_body):
    global_scope = {}
    targets = {}
    for match in re.finditer(global_variable, all_body, flags=re.MULTILINE):
        global_scope[match.group('name')] = match.group('value')

    for match in re.finditer(target, all_body, flags=re.MULTILINE):
        local_scope = {}
        commands = []
        docstring_value = ''
        name = match.group('name')
        dependencies = re.findall(identifier, match.group('dependencies'))
        body = [m.group('value') for m in re.finditer(indented_line_group, match.group('body'))]
        for line in body:
            if not docstring_value:
                match = re.match(docstring, line)
                if match is not None:
                    docstring_value = match.group('value')
                    continue
            match = re.match(global_variable, line)
            if match is not None:
                local_scope[match.group('name')] = match.group('value')
                continue
            match = re.match(comment, line)
            if match is not None:
                continue
            commands.append(line)

        targets[name] = Target(name, dependencies, docstring_value, commands, local_scope)

    return global_scope, targets


class Target:
    def __init__(self, name, dependencies, docstring=None, commands=None, local_scope=None):
        self.name = name
        self.dependencies = dependencies
        self.docstring = docstring or self.name
        self.commands = commands or []
        self.local_scope = local_scope or {}

    def __repr__(self):
        return "<Target {} deps: {}>".format(self.name, self.dependencies)

    def execute(self, global_scope):
        scope = global_scope.copy()
        scope.update(self.local_scope)
        scope.update(os.environ)
        scope['argv'] = ' '.join(sys.argv[2:])
        for command in self.commands:
            formatted_command = command.format(**scope)
            print(">>>", formatted_command)
            os.system(formatted_command)

    def description(self):
        return  "{}: {} deps: {}".format(self.name, self.docstring, self.dependencies)



def kahn(dependency_tree):
    dependency_tree = copy.deepcopy(dependency_tree)
    zero_degree_nodes = {node for node, deps in dependency_tree.items() if not deps}
    non_zero_nodes = {node: deps for node, deps in dependency_tree.items() if deps}
    result = []
    while zero_degree_nodes:
        n = zero_degree_nodes.pop()
        result.append(n)
        for node, deps in non_zero_nodes.items():
            if n in deps:
                deps.remove(n)
        new_zero_degree_nodes = {node for node, deps in non_zero_nodes.items() if not deps}
        zero_degree_nodes.update(new_zero_degree_nodes)
        non_zero_nodes = {node: deps for node, deps in non_zero_nodes.items() if deps}
    if non_zero_nodes:
        raise Exception('dependency_tree has cycles')

    return result


def cut(target, graph):
    """Makes a cut of a full dependency graph"""
    output = {}
    to_process = [target]
    while to_process:
        current = to_process.pop(0)
        output[current] = graph[current]
        for dep in graph[current]:
            if dep not in output:
                to_process.append(dep)

    return output


if __name__ == "__main__":
    with open('Runfile') as fh:
        all_body = fh.read()
    global_scope, targets = parse(all_body)

    dependency_tree = {
        target.name: set(target.dependencies)
        for target in targets.values()
    }
    for deps in dependency_tree.values():
        for dep in deps:
            assert dep in dependency_tree

    kahn(dependency_tree)

    # Cut graph by required target
    try:
        dependencies = kahn(cut(sys.argv[1], dependency_tree))
    except IndexError:
        print("\n".join((t.description() for t in targets.values())))
        raise SystemExit(2)

    for target in dependencies:
        print('-------- Running target: {} -------------'.format(target))
        targets[target].execute(global_scope)

