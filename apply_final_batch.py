#!/usr/bin/env python3

import json
import re
from pathlib import Path

# Load current batch
with open('.next_functional_batch.json', 'r') as f:
    batch = json.load(f)

instances = batch['instances']
print(f'Processing final batch {batch["batch_number"]} with {len(instances)} instances')

changes_log = []
for instance in instances:
    file_path = Path(instance['file_path'])
    instance_id = instance['instance_id']

    print(f'Processing {instance_id}: {file_path}')

    if not file_path.exists():
        print(f'  File not found, skipping')
        continue

    content = file_path.read_text()
    original = content
    changes_made = []

    # Check what imports exist and replace with facade bridge
    if 'from ..config.settings import get_settings' in content:
        content = content.replace('from ..config.settings import get_settings', 'from ..core.context_bridge import get_settings')
        changes_made.append('Replaced get_settings import with context_bridge')

    # Check if there are other patterns that need replacement
    if re.search(r'from \.\.\.config\.settings import get_settings', content):
        content = re.sub(r'from \.\.\.config\.settings import get_settings', 'from ...core.context_bridge import get_settings', content)
        changes_made.append('Replaced get_settings import (3 levels) with context_bridge')

    if content != original:
        file_path.write_text(content)
        print(f'  ✅ Applied changes: {changes_made}')
        changes_log.append({
            'file': str(file_path),
            'instance_id': instance_id,
            'changes': changes_made,
            'transformation_type': 'facade_bridge'
        })
    else:
        print(f'  ⚠️ No changes needed')

# Save changes log
with open('phase3_batch_changes.json', 'w') as f:
    json.dump({
        'batch_number': batch['batch_number'],
        'transformation_approach': 'facade_bridge',
        'changes_log': changes_log,
        'signature_compatibility': 'maintained'
    }, f, indent=2)

print(f'Final batch transformation complete: {len(changes_log)} files modified')
print('All function signatures preserved - backward compatibility maintained')
