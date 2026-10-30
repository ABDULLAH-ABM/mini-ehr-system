# Mini EHR (Electronic Health Record) Demo

A small command-line electronic health record system built with **Python** and **SQLite**. It demonstrates core e-health concepts: patient registry, appointments, clinical records, **role-based access control**, and an **audit trail** of every access attempt.

> **Disclaimer:** educational demo using fictional data only. The `--user` option is not real authentication. Never store real patient data in it.

## Features
- Patients, appointments and clinical records (related tables with foreign keys)
- Four roles with different permissions: `admin`, `doctor`, `nurse`, `receptionist`
- Every action, allowed or denied, is written to an audit log
- Standard library only, with unit tests

## Role permissions
| Action | admin | doctor | nurse | receptionist |
|---|:-:|:-:|:-:|:-:|
| Add / view patients | yes | view | yes | yes |
| Book / view appointments | yes | yes | view | yes |
| Add clinical records | yes | yes | no | no |
| View clinical records | yes | yes | yes | no |
| View audit log | yes | no | no | no |

## Usage
```bash
python mini_ehr.py init
python mini_ehr.py --user reception_demo add-patient "Test Person" --dob 2000-05-20
python mini_ehr.py --user dr_demo add-record 1 --diagnosis "Seasonal flu" --notes "Rest and fluids"
python mini_ehr.py --user dr_demo records 1
python mini_ehr.py --user reception_demo records 1   # denied and logged
python mini_ehr.py --user admin1 audit
```

## Run the tests
```bash
python -m unittest -v
```

## Skills demonstrated
Health information systems concepts (privacy, least privilege, auditability), relational database design, access-control logic, Python scripting, unit testing.

## License
MIT
