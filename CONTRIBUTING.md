# Contributing to ErgoLabs

Thanks for your interest in contributing. ErgoLabs is open source, and we
welcome contributions from the research community and beyond — bug reports,
fixes, features, documentation, and discussion.

This document explains how to contribute and, importantly, the **Developer
Certificate of Origin (DCO)** sign-off we require on every commit.

## License

ErgoLabs is licensed under the **GNU Affero General Public License v3.0
(AGPLv3)**. By contributing, you agree that your contributions are licensed
under AGPLv3, consistent with the project as a whole. See the [`LICENSE`](LICENSE)
file for the full text.

The AGPLv3 guarantees that ErgoLabs and all future derivatives, improvements,
and adaptations remain open and available — including when the software is run
as a network service. This is intentional: it keeps the project's source
permanently inspectable and reproducible, which matters for scientific work.

## Developer Certificate of Origin (DCO)

We use the **Developer Certificate of Origin** instead of a Contributor
License Agreement. There is no form to sign and no paperwork. You certify the
origin of your contribution by adding a `Signed-off-by` line to each commit.

The full DCO text is in the [`DCO`](DCO) file in this repository (the canonical
Developer Certificate of Origin, version 1.1, from
<https://developercertificate.org>). In short, signing off certifies that you
wrote the contribution or otherwise have the right to submit it under the
project's open source license.

### How to sign off

Add the `-s` flag when you commit:

```
git commit -s -m "Short description of the change"
```

This appends a line to your commit message in exactly this form:

```
Signed-off-by: Your Name <your.email@example.com>
```

Use your real name and a real email address. **The sign-off email must match
the commit author email** — a mismatch is the most common reason the automated
check fails.

You can configure your identity once so it's consistent:

```
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Fixing a missing sign-off

If you forgot to sign off:

- **Last commit only:**

  ```
  git commit --amend -s --no-edit
  ```

- **Multiple commits:** start an interactive rebase over the range and add the
  sign-off to each commit:

  ```
  git rebase --signoff main
  ```

  (Replace `main` with the branch you opened your pull request against.)

After amending or rebasing, you will need to force-push your branch:

```
git push --force-with-lease
```

The DCO check on your pull request will re-run automatically and should pass
once every commit is signed off.

## How to contribute

1. **Open an issue first** for anything non-trivial. For bugs, include steps to
   reproduce, expected vs. actual behavior, and your environment. For features,
   describe the use case before the implementation — it saves everyone time.
2. **Fork the repository** and create a branch from `main` with a descriptive
   name (e.g. `fix/scheduler-race`, `feature/export-csv`).
3. **Make your changes** in focused commits. Keep unrelated changes in separate
   pull requests.
4. **Sign off every commit** as described above.
5. **Run the tests** locally and add tests for new behavior where it makes
   sense.
6. **Open a pull request** against `main`. Describe what changed and why, and
   link any related issue. The DCO check must pass before a maintainer can
   merge.

## Code review

Maintainers will review your pull request and may ask for changes. Reviews are
about the code, not the contributor — please don't take requested changes
personally, and feel free to push back with reasoning if you disagree.

## Reporting security issues

Please do **not** open a public issue for security vulnerabilities. Instead,
contact the maintainers privately at **security@ergolabs.example** (replace with
your real address) so the issue can be addressed before public disclosure.

## Questions

If anything here is unclear, open a discussion or an issue. We'd rather answer a
question than have you guess.