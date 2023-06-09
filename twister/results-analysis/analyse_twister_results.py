#!/usr/bin/env python3
"""Analyse json's twister output file and generate readable report."""

import argparse
import json
import sys
import os


def gh_error(msg):
    """Display error message in github action log."""
    print(f"::error ::{msg}")

def gh_notice(msg):
    """Display error message in github action log."""
    print(f"::notice ::{msg}")


def md_report_header():
    """Return markdown array header for test configurations."""
    res = "| status | scenario | platform | failure reason |\n"
    res += "| --- | --- | --- | :--- |\n"
    return res


def md_result(result):
    """Return markdown string for result."""

    if result == "passed":
        return f":heavy_check_mark: {result}"
    if result == "error":
        return f":x: {result}"
    return f"{result}"


def md_report_test_config(test_config):
    """Analyse one test config and return markdown formatted result."""
    scenario = test_config['name']
    platform = test_config['platform']
    status = test_config['status']
    if 'reason' in test_config:
        reason = test_config['reason']
    else:
        reason = " "
    res = f"| {md_result(status)} | {scenario} | {platform} | {reason} |\n"
    return res


def gh_log_report_test_config(test_config):
    """Analyse one test config and display formatted log for github action."""
    scenario = test_config['name']
    platform = test_config['platform']
    status = test_config['status']
    if 'reason' in test_config:
        reason = test_config['reason']
    else:
        reason = " "

    msg = f"{status} : {scenario} {platform=} {reason}"
    if status == 'error':
        gh_error(msg)
    elif status == 'passed':
        print(msg)
    else:
        gh_notice(msg)


def analyse_test_suite(testsuite, fd_out):
    """Analyse twister testsuite.

    The analysis is written in the provided file descriptor.

    Return True when no test config failed, False otherwise
    """
    success = True
    for test_config in testsuite:
        if test_config['status'] != "passed":
            success = False

    fd_out.write("### Overall status\n")
    if not success:
        fd_out.write(":x: Failures in at least one test config.\n")
    else:
        fd_out.write(":heavy_check_mark: All tests configs passed.\n")

    fd_out.write("\n")
    fd_out.write("### Detailed status\n")
    fd_out.write(md_report_header())
    for test_config in testsuite:
        fd_out.write(md_report_test_config(test_config))
        gh_log_report_test_config(test_config)

    return success


def analyse_twister_json(twister_json, fd_out):
    """Analyse Twister Json File.

    The analysis is written in the provided file descriptor.

    Return True when no test config failed, False otherwise.
    """
    twister_folder = os.path.basename(os.path.dirname(twister_json))
    fd_out.write(f"## {twister_folder}\n")
    with open(twister_json, 'r', encoding='utf-8') as json_fd:
        content = json_fd.read()
        twister_result = json.loads(content)
        return analyse_test_suite(twister_result['testsuites'], fd_out)


def main():
    """Main script function."""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("twister_json", type=str,
                        help="Path to twister.json file generated by twister.")
    parser.add_argument("--file-report", type=str,
                        help="File where report is written, default to stdout.",
                        default="-")
    fail_help = "Return a non-zero error code if there was an error in one of the test config."
    parser.add_argument("--fail", action='store_true',
                        help=fail_help)
    args = parser.parse_args()
    if args.file_report != "-":
        # pylint: disable-next=consider-using-with
        fd_out = open(args.file_report, 'a', encoding='utf-8')
    else:
        fd_out = sys.stdout

    res = analyse_twister_json(args.twister_json, fd_out)
    if not res:
        sys.stderr.write("An error occurred in one of the tests configs.\n")
        if args.fail:
            sys.exit(1)


if __name__ == "__main__":
    main()
