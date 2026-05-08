#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

DATA_DIR = Path("domain-list-community/data")
OUTPUT_DIR = Path("./mrs")

OUTPUT_DIR.mkdir(exist_ok=True)

cn_rules = set()
not_cn_rules = set()


def add_rule(target: set, rule: str):
    rule = rule.strip()

    if not rule:
        return

    if rule.startswith("regexp:"):
        return

    # full:google.com
    if rule.startswith("full:"):
        target.add("DOMAIN," + rule[5:])
        return

    # keyword:google
    if rule.startswith("keyword:"):
        target.add("DOMAIN-KEYWORD," + rule[8:])
        return

    # domain:google.com
    if rule.startswith("domain:"):
        target.add("+." + rule[7:])
        return

    target.add("+." + rule)


def parse_file(
    name: str,
    target: set,
    attr_filter: str | None = None,
    exclude_attr: str | None = None,
    opposite_target: set | None = None,
    visited: set | None = None,
):
    """
    attr_filter:  Positive filter — only include domains tagged with this attr.
                  e.g. "cn" means only keep "@cn" domains.

    exclude_attr: Negative filter — domains tagged with this attr are
                  redirected to opposite_target instead of being discarded.

    Include-level syntax:
      include:foo           → inherit parent's filters
      include:foo @cn       → positive filter "cn" (only @cn domains)
      include:foo @-!cn     → negative filter "!cn" (redirect @!cn to opposite)
    """

    if visited is None:
        visited = set()

    key = (name, attr_filter, exclude_attr)
    if key in visited:
        return
    visited.add(key)

    file_path = DATA_DIR / name

    if not file_path.exists():
        print(f"  skip missing: {name}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.split("#")[0].strip()

            if not line:
                continue

            # include
            if line.startswith("include:"):
                include_line = line.replace("include:", "", 1).strip()

                if " @" in include_line:
                    include_name, include_attr = include_line.rsplit(" @", 1)
                    include_name = include_name.strip()
                    include_attr = include_attr.strip()

                    if include_attr.startswith("-"):
                        # negative filter: include:xxx @-!cn
                        # => redirect @!cn domains to opposite_target
                        parse_file(
                            include_name,
                            target,
                            attr_filter=None,
                            exclude_attr=include_attr[1:],  # strip leading '-'
                            opposite_target=opposite_target,
                            visited=visited,
                        )
                    else:
                        # positive filter: include:xxx @cn  or  include:xxx @ads
                        # => only include domains tagged with cn (or ads)
                        parse_file(
                            include_name,
                            target,
                            attr_filter=include_attr,
                            exclude_attr=None,
                            opposite_target=opposite_target,
                            visited=visited,
                        )
                else:
                    # inherits parent filters
                    parse_file(
                        include_line,
                        target,
                        attr_filter=attr_filter,
                        exclude_attr=exclude_attr,
                        opposite_target=opposite_target,
                        visited=visited,
                    )

                continue

            # domain rule
            if " @" in line:
                parts = line.split(" @")
                rule = parts[0].strip()
                attrs = set(p.strip() for p in parts[1:])
            else:
                rule = line.strip()
                attrs = set()

            # positive filter: only include domains with this attr
            if attr_filter is not None:
                if attr_filter not in attrs:
                    continue

            # negative filter: redirect to opposite_target instead of discarding
            if exclude_attr is not None:
                if exclude_attr in attrs:
                    if opposite_target is not None:
                        add_rule(opposite_target, rule)
                    continue

            add_rule(target, rule)


def write_yaml(path: Path, rules: set):
    with open(path, "w", encoding="utf-8") as f:
        f.write("payload:\n")
        for rule in sorted(rules):
            f.write(f"  - {rule}\n")


def generate_accelerated_domains():
    input_files = [
        "dnsmasq-china-list/accelerated-domains.china.conf",
        "dnsmasq-china-list/apple.china.conf",
        "dnsmasq-china-list/google.china.conf",
    ]

    rules = set()

    for file_path in input_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line.startswith("server=/"):
                        continue
                    parts = line.split("/")
                    if len(parts) < 2:
                        continue
                    domain = parts[1].strip()
                    if domain:
                        rules.add(f"+.{domain}")
            print(f"  processed: {file_path}")
        except FileNotFoundError:
            print(f"  skip missing: {file_path}")

    write_yaml(OUTPUT_DIR / "accelerated-domains.yaml", rules)


def main():
    print("=== resolve geolocation-cn ===")
    parse_file("geolocation-cn", cn_rules, exclude_attr="!cn", opposite_target=not_cn_rules)

    print("=== resolve geolocation-!cn ===")
    parse_file("geolocation-!cn", not_cn_rules, exclude_attr="cn", opposite_target=cn_rules)

    write_yaml(OUTPUT_DIR / "cn.yaml", cn_rules)
    write_yaml(OUTPUT_DIR / "not-cn.yaml", not_cn_rules)

    generate_accelerated_domains()

    print(f"\n=== done ===")
    print(f"  cn:     {len(cn_rules)} rules")
    print(f"  not-cn: {len(not_cn_rules)} rules")


if __name__ == "__main__":
    main()
