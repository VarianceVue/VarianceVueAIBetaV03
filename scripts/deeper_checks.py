"""
Deeper checks: submittal-review pairing, NTP logic, cofferdam segments, DSM production.
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DOCS = os.path.join(os.path.dirname(__file__), '..', 'docs')

def load(name):
    with open(os.path.join(DOCS, f'xer_{name}.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

tasks = load('TASK')
preds = load('TASKPRED')
cals = load('CALENDAR')

cal_names = {c['clndr_id']: c['clndr_name'] for c in cals}
task_by_id = {t['task_id']: t for t in tasks}

succ_map = {}
pred_map = {}
for p in preds:
    succ_map.setdefault(p['pred_task_id'], []).append(p)
    pred_map.setdefault(p['task_id'], []).append(p)

print("=" * 100)
print("1. SUBMITTAL vs APPROVAL PAIRING CHECK")
print("=" * 100)
submittals = [t for t in tasks if t.get('task_code', '').startswith('SU-')]
approvals = [t for t in tasks if t.get('task_code', '').startswith('AP-')]
print(f"  Submittals (SU-): {len(submittals)}")
print(f"  Approvals (AP-): {len(approvals)}")

for s in submittals:
    s_num = s.get('task_code', '').replace('SU-', '')
    matching_ap = [a for a in approvals if s_num in a.get('task_code', '')]
    s_dur = float(s.get('target_drtn_hr_cnt', '0')) / 8
    print(f"  {s.get('task_code',''):15} {s.get('task_name','')[:55]:56} dur={s_dur:>4.0f} WD  cal={cal_names.get(s.get('clndr_id',''), '')[:30]}")
    if matching_ap:
        for a in matching_ap:
            a_dur = float(a.get('target_drtn_hr_cnt', '0')) / 8
            print(f"    -> {a.get('task_code',''):12} {a.get('task_name','')[:55]:56} dur={a_dur:>4.0f} WD")
    else:
        print(f"    -> NO MATCHING APPROVAL FOUND")

print()
print("=" * 100)
print("2. COFFERDAM SEGMENTS vs SPEC COVERAGE")
print("=" * 100)
cfd_tasks = [t for t in tasks if 'cfd' in t.get('task_code', '').lower() or 'combi' in t.get('task_name', '').lower() or 'cofferdam' in t.get('task_name', '').lower()]
for t in cfd_tasks:
    dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
    cal = cal_names.get(t.get('clndr_id', ''), '')[:30]
    print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:65]:66} dur={dur:>4.0f} WD  cal={cal}")

print()
print("=" * 100)
print("3. DSM PRODUCTION ACTIVITIES")
print("=" * 100)
dsm_tasks = [t for t in tasks if 'dsm' in t.get('task_code', '').lower() or 'deep soil' in t.get('task_name', '').lower() or 'soil mixing' in t.get('task_name', '').lower()]
for t in dsm_tasks:
    dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
    cal = cal_names.get(t.get('clndr_id', ''), '')[:30]
    tf = float(t.get('total_float_hr_cnt', '0')) / 8
    print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:65]:66} dur={dur:>4.0f} WD  TF={tf:>4.0f}  cal={cal}")

print()
print("=" * 100)
print("4. SPOIL REMOVAL ACTIVITIES")
print("=" * 100)
spoil_tasks = [t for t in tasks if 'spoil' in t.get('task_name', '').lower()]
for t in spoil_tasks:
    dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
    cal = cal_names.get(t.get('clndr_id', ''), '')[:30]
    print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:65]:66} dur={dur:>4.0f} WD  cal={cal}")

print()
print("=" * 100)
print("5. OBSTRUCTION REMOVAL ACTIVITIES")
print("=" * 100)
obs_tasks = [t for t in tasks if 'obstruct' in t.get('task_name', '').lower() or 'obs' in t.get('task_code', '').lower()]
for t in obs_tasks:
    dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
    cal = cal_names.get(t.get('clndr_id', ''), '')[:30]
    tf = float(t.get('total_float_hr_cnt', '0')) / 8
    print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:65]:66} dur={dur:>4.0f} WD  TF={tf:>4.0f}  cal={cal}")

print()
print("=" * 100)
print("6. CRITICAL PATH (TF=0) ACTIVITIES")
print("=" * 100)
crit = [t for t in tasks if float(t.get('total_float_hr_cnt', '0')) == 0 and t.get('task_type', '') != 'TT_Mile']
for t in sorted(crit, key=lambda x: x.get('early_start_date', x.get('target_start_date', '9999'))):
    dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
    es = t.get('early_start_date', t.get('target_start_date', ''))[:10]
    ef = t.get('early_end_date', t.get('target_end_date', ''))[:10]
    print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:60]:61} dur={dur:>4.0f}  {es} - {ef}")

print()
print("=" * 100)
print("7. ACTIVITIES ON 7-DAY CALENDAR")
print("=" * 100)
for t in tasks:
    cal = cal_names.get(t.get('clndr_id', ''), '')
    if '7/8' in cal or '7-day' in cal.lower():
        dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
        print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:55]:56} dur={dur:>4.0f} WD  cal={cal[:35]}")

print()
print("=" * 100)
print("8. DEWATERING ACTIVITIES")
print("=" * 100)
dewater = [t for t in tasks if 'dewat' in t.get('task_name', '').lower()]
if not dewater:
    print("  NONE FOUND - Dewatering is missing from the schedule")
else:
    for t in dewater:
        dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
        print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:60]:61} dur={dur:>4.0f}")

print()
print("=" * 100)
print("9. TOP FILL ACTIVITIES")
print("=" * 100)
topfill = [t for t in tasks if 'top fill' in t.get('task_name', '').lower() or 'topfill' in t.get('task_name', '').lower()]
if not topfill:
    print("  NONE FOUND")
else:
    for t in topfill:
        dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
        print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:60]:61} dur={dur:>4.0f}")

print()
print("=" * 100)
print("10. SCOUR PROTECTION ACTIVITIES")
print("=" * 100)
scour = [t for t in tasks if 'scour' in t.get('task_name', '').lower()]
for t in scour:
    dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
    cal = cal_names.get(t.get('clndr_id', ''), '')[:30]
    print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:60]:61} dur={dur:>4.0f}  cal={cal}")

print()
print("=" * 100)
print("11. COMPLIANCE (SITE CONTROLS, BUOYS)")
print("=" * 100)
comp = [t for t in tasks if 'compliance' in t.get('task_name', '').lower() or 'buoy' in t.get('task_name', '').lower() or 'site control' in t.get('task_name', '').lower()]
for t in comp:
    dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
    print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:60]:61} dur={dur:>4.0f}")

print()
print("=" * 100)
print("12. NTP MILESTONES")
print("=" * 100)
ntp = [t for t in tasks if 'ntp' in t.get('task_name', '').lower() or 'notice to proceed' in t.get('task_name', '').lower() or 'notice of award' in t.get('task_name', '').lower()]
for t in ntp:
    dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
    es = t.get('early_start_date', t.get('target_start_date', ''))[:10]
    ef = t.get('early_end_date', t.get('target_end_date', ''))[:10]
    tt = t.get('task_type', '')
    print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:60]:61} type={tt}  dur={dur:>4.0f}  {es} - {ef}")

print()
print("=" * 100)
print("13. CLOSEOUT/FINAL/AS-BUILT ACTIVITIES")
print("=" * 100)
close = [t for t in tasks if any(x in t.get('task_name', '').lower() for x in ['closeout', 'close out', 'final', 'as-built', 'as built', 'demob', 'punch', 'warranty', 'record doc'])]
for t in close:
    dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
    es = t.get('early_start_date', t.get('target_start_date', ''))[:10]
    ef = t.get('early_end_date', t.get('target_end_date', ''))[:10]
    print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:60]:61} dur={dur:>4.0f}  {es} - {ef}")

print()
print("=" * 100)
print("14. STURGEON/FISH SURVEY ACTIVITIES")
print("=" * 100)
fish = [t for t in tasks if 'sturgeon' in t.get('task_name', '').lower() or 'fish' in t.get('task_name', '').lower()]
if not fish:
    print("  NONE FOUND - Sturgeon monitoring activities are missing")
else:
    for t in fish:
        dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
        print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:60]:61} dur={dur:>4.0f}")

print()
print("=" * 100)
print("15. TURBIDITY CURTAIN ACTIVITIES")
print("=" * 100)
turb = [t for t in tasks if 'turbid' in t.get('task_name', '').lower() or 'curtain' in t.get('task_name', '').lower()]
if not turb:
    print("  NONE FOUND - Turbidity curtain activities are missing")
else:
    for t in turb:
        dur = float(t.get('target_drtn_hr_cnt', '0')) / 8
        print(f"  {t.get('task_code',''):15} {t.get('task_name','')[:60]:61} dur={dur:>4.0f}")

print()
print("=" * 100)
print("16. SS AND FF RELATIONSHIP DETAILS")
print("=" * 100)
for p in preds:
    if p.get('pred_type') in ('PR_SS', 'PR_FF'):
        pred_t = task_by_id.get(p['pred_task_id'], {})
        succ_t = task_by_id.get(p['task_id'], {})
        lag = float(p.get('lag_hr_cnt', '0')) / 8
        print(f"  {p['pred_type']:4}  {pred_t.get('task_code',''):15} -> {succ_t.get('task_code',''):15}  lag={lag:>4.0f}  ({pred_t.get('task_name','')[:40]} -> {succ_t.get('task_name','')[:40]})")
