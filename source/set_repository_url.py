#!/usr/bin/env python3
"""Set paper availability only after verifying an existing public project repo."""
import argparse
import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def set_url(url):
    match = re.fullmatch(r'https://github\.com/([A-Za-z0-9-]+)/([A-Za-z0-9_.-]+)/?', url)
    if not match:
        raise SystemExit('Use the actual https://github.com/OWNER/REPOSITORY URL.')
    owner, name = match.groups()
    request = urllib.request.Request(f'https://api.github.com/repos/{owner}/{name}',
                                    headers={'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        repository = json.load(response)
    assert not repository['private'], 'Repository is not public.'
    canonical = repository['html_url'].rstrip('/')
    branch = repository['default_branch']
    # Verify that the publication contains this project, not just an empty repo.
    request = urllib.request.Request(f'https://api.github.com/repos/{owner}/{name}/contents/source/audit_pipeline.py?ref={branch}')
    with urllib.request.urlopen(request, timeout=30) as response:
        entry = json.load(response)
    assert entry['type'] == 'file'
    request = urllib.request.Request(f'https://api.github.com/repos/{owner}/{name}/contents/splits/metadata.json?ref={branch}')
    with urllib.request.urlopen(request, timeout=30) as response:
        split = json.load(response)
    import base64
    metadata = json.loads(base64.b64decode(split['content']))
    assert metadata['dataset_sha256'] == '62ec5d632c9e665851c551487d6d1e2afbc7f8f55b62cac4649999dadafc89de'
    text = ('Source, frozen split indices, saved row-level predictions, and reproduction instructions are publicly available at '
            + r'\url{' + canonical + '}. The accompanying submission archive also includes the audited data and VM evidence.\n')
    (ROOT / 'report/code_availability.tex').write_text(text)
    (ROOT / 'CODE_AVAILABILITY.json').write_text(json.dumps({
        'status': 'public_verified', 'url': canonical,
        'verified_contents': ['source/audit_pipeline.py', 'splits/metadata.json'],
        'scope': 'Public repository and project split identity verified; recompile reports after setting URL.'}, indent=2) + '\n')
    citation = ROOT / 'CITATION.cff'
    lines = [line for line in citation.read_text().splitlines() if not line.startswith('repository-code:')]
    citation.write_text('\n'.join(lines) + f'\nrepository-code: "{canonical}"\n')
    print('Verified public project repository and updated paper availability:', canonical)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url')
    args = parser.parse_args()
    set_url(args.url)
