"""
Parse P6 XER file and extract key schedule data for review.
Outputs JSON files for activities, WBS, relationships, calendars, constraints.
"""
import sys
import json
import os

def parse_xer(filepath):
    tables = {}
    current_table = None
    fields = None

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.rstrip('\n').rstrip('\r')
            if line.startswith('%T\t'):
                current_table = line.split('\t')[1].strip()
                tables[current_table] = []
                fields = None
            elif line.startswith('%F\t') and current_table:
                fields = line.split('\t')[1:]
            elif line.startswith('%R\t') and current_table and fields:
                values = line.split('\t')[1:]
                row = {}
                for i, field in enumerate(fields):
                    row[field] = values[i] if i < len(values) else ''
                tables[current_table].append(row)

    return tables


def main():
    xer_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(xer_path)

    tables = parse_xer(xer_path)

    print(f"Tables found: {list(tables.keys())}")
    for tname, rows in tables.items():
        print(f"  {tname}: {len(rows)} rows")

    for tname in ['PROJECT', 'PROJWBS', 'TASK', 'TASKPRED', 'CALENDAR', 'TASKACTV',
                   'ACTVCODE', 'ACTVTYPE', 'ACCOUNT', 'RSRC', 'TASKRSRC', 'UDFVALUE',
                   'UDFTYPE', 'SCHEDOPTIONS', 'PROJPCAT', 'MEMOTYPE']:
        if tname in tables:
            outfile = os.path.join(out_dir, f'xer_{tname}.json')
            with open(outfile, 'w', encoding='utf-8') as f:
                json.dump(tables[tname], f, indent=2, ensure_ascii=False)
            print(f"  Wrote {outfile} ({len(tables[tname])} rows)")


if __name__ == '__main__':
    main()
