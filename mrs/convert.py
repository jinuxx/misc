#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate cn and not-cn mrs from v2fly/domain-list-community"""


def main() -> None:
    cn_mrs = []
    cn_include = ['geolocation-cn']

    not_cn_mrs = []
    not_cn_include = ['geolocation-!cn']
    while len(cn_include) != 0:
        rule_name = cn_include.pop(0)
        with open(f'domain-list-community/data/{rule_name}', 'r') as cn:
            for row in cn:
                line = row.split("#")[0].strip()
                if len(line) == 0 or line.startswith('regexp:'):
                    continue
                if line.startswith('include'):
                    cn_include.append(line.split("#")[0].strip().replace('include:', '').replace(' @-!cn', ''))
                    continue
                if '@' in line:
                    rule = line.split("@")[0].strip()
                    attr = line.split("@")[1].strip()
                    if attr == '!cn':
                        if rule.startswith('full:'):
                            not_cn_mrs.insert(0, rule.replace('full:', 'DOMAIN,'))
                        else:
                            not_cn_mrs.append(f'+.{rule}')
                    continue
                if line.startswith('full:'):
                    cn_mrs.insert(0, line.replace('full:', 'DOMAIN,'))
                    continue
                cn_mrs.append(f'+.{line}')
    
    while len(not_cn_include) != 0:
        rule_name = not_cn_include.pop(0)
        with open(f'domain-list-community/data/{rule_name}', 'r') as not_cn:
            for row in not_cn:
                line = row.split("#")[0].strip()
                if len(line) == 0 or line.startswith('regexp:'):
                    continue
                if line.startswith('include'):
                    not_cn_include.append(line.split("#")[0].strip().replace('include:', ''))
                    continue
                if '@' in line:
                    rule = line.split("@")[0].strip()
                    attr = line.split("@")[1].strip()
                    if attr == 'cn':
                        if rule.startswith('full:'):
                            cn_mrs.insert(0, rule.replace('full:', 'DOMAIN,'))
                        else:
                            cn_mrs.append(f'+.{rule}')
                    continue
                if line.startswith('full:'):
                    not_cn_mrs.insert(0, line.replace('full:', 'DOMAIN,'))
                    continue
                not_cn_mrs.append(f'+.{line}')
    
    with open('./mrs/cn.yaml', 'w') as yaml:
        yaml.write('payload:\n  - ')
        yaml.write('\n  - '.join(cn_mrs))

    with open('./mrs/not-cn.yaml', 'w') as yaml:
        yaml.write('payload:\n  - ')
        yaml.write('\n  - '.join(not_cn_mrs))
    
    print(cn_include)
    print(not_cn_include)

if __name__ == "__main__":
    main()