# Signing-sheet images

The five signing-sheet photos, named by date (ISO `YYYY-MM-DD`) so `sams.py`
keys each sheet automatically:

| File | Date | Hall |
|------|------|------|
| `2019-05-31.jpeg` | 31 May 2019 | 106 |
| `2019-06-21.jpeg` | 21 Jun 2019 | Hall-106 |
| `2019-06-28.jpeg` | 28 Jun 2019 | Hall-106 |
| `2019-07-05.jpeg` | 05 Jul 2019 | L104 |
| `2019-07-12.jpeg` | 12 Jul 2019 | Hall-103 |

## Process them

```bash
# one sheet
python sams.py data/sheets/2019-05-31.jpeg data/info.xml

# all five (bash)
for f in data/sheets/*.jpeg; do python sams.py "$f" data/info.xml; done
```

```powershell
# all five (PowerShell)
Get-ChildItem data/sheets/*.jpeg | ForEach-Object { python sams.py $_.FullName data/info.xml }
```

## Verified attendance results (present ✓ / absent ✗)

Confirmed by eye against the physical sheets — useful as ground truth for the
report's testing section:

| Student | 05-31 | 06-21 | 06-28 | 07-05 | 07-12 |
|---------|:---:|:---:|:---:|:---:|:---:|
| 10000409 Dilshanika | ✓ | ✓ | ✓ | ✓ | ✓ |
| 10009301 Shehan | ✓ | ✓ | ✗ | ✗ | ✓ |
| 10009302 Chithrananda | ✓ | ✓ | ✗ | ✓ | ✓ |
| 10009303 De Silva | ✓ | ✓ | ✓ | ✗ | ✓ |
| 10009304 Udara | ✓ | ✓ | ✓ | ✓ | ✓ |
| 10009306 Hansa | ✓ | ✓ | ✓ | ✓ | ✓ |

> Note: on `2019-06-21`, student 10009306 wrote the word "ab" in the signature
> cell (not a signature). Because it is ink, the system reads it as *present* —
> a good real-world edge case to discuss in the report's challenges section.
