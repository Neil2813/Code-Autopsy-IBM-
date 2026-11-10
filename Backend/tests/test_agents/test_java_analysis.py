import json
import shutil

import pytest

from app.agents.agent_nodes import _detect_java_issues
from app.agents.java_compiler import detect_java_compiler_issues
from app.llm.rule_based_provider import RuleBasedProvider


@pytest.mark.skipif(shutil.which("javac") is None, reason="javac is required for compiler diagnostics")
def test_java_compiler_reports_syntax_name_type_and_data_flow_errors():
    syntax_issues = detect_java_compiler_issues([{
        "file_path": "Syntax.java",
        "language": "java",
        "content": 'class Syntax { void run() { System.out.println("x") addRecord("x") } }',
    }])
    assert len([issue for issue in syntax_issues if issue["category"] == "syntax"]) >= 2

    semantic_issues = detect_java_compiler_issues([{
        "file_path": "Types.java",
        "language": "java",
        "content": '''
import java.util.ArrayList;
import java.util.List;
class Types {
    static void deleteRecord(String id) {}
    void run(boolean condition) {
        List<String> records = new ArrayList<>();
        for (int i = 0; i <= records.size(); i++) {
            System.out.println(record.get(i));
            deleteRecord(i);
        }
        int result = "100" + 50;
        System.out.println(results);
        int maybeUninitialized;
        if (condition) maybeUninitialized = 1;
        System.out.println(maybeUninitialized);
    }
}
''',
    }])
    categories = {issue["category"] for issue in semantic_issues}
    titles = {issue["title"] for issue in semantic_issues}
    assert {"undefined_symbol", "type_mismatch"} <= categories
    assert "Undefined variable: record" in titles
    assert "Undefined variable: results" in titles

    data_flow_issues = detect_java_compiler_issues([{
        "file_path": "Flow.java",
        "language": "java",
        "content": '''
class Flow {
    void run(boolean condition) {
        int maybeUninitialized;
        if (condition) maybeUninitialized = 1;
        System.out.println(maybeUninitialized);
    }
}
''',
    }])
    assert any(issue["category"] == "data_flow" for issue in data_flow_issues)


def test_scanner_token_read_followed_by_nextline_is_a_medium_heuristic():
    issues = _detect_java_issues({
        "file_path": "InputDemo.java",
        "content": '''
import java.util.Scanner;
class InputDemo {
    void run(Scanner input) {
        int choice = input.nextInt();
        String name = input.nextLine();
    }
}
''',
    })

    finding = next(issue for issue in issues if issue["pattern_key"] == "scanner_nextline_after_token_read")
    assert finding["category"] == "input_handling"
    assert finding["level"] == "medium"


def test_rule_based_fallback_does_not_invent_generic_legacy_finding():
    response = json.loads(RuleBasedProvider()._generate_risk_json(""))

    assert response["issues"] == []