# Local merge / rebuild incident flow

Use when a refactor is significant enough to deserve a durable incident note, local merge to `main`, push to the authorized remotes, and a post-merge rebuild / validation.

## Checklist
1. Create an `agent/<topic>` branch.
2. Make the smallest coherent patch set.
3. Add a short incident note under `docs/incidents/YYYY-MM-DD-<slug>.md` if the change alters runtime behavior or prunes a subsystem.
4. Run the focused test slice first.
5. Run a syntax/compile sanity check for touched Python files.
6. Commit with a conventional message.
7. Merge back to `main` locally with fast-forward when possible.
8. Push each authorized remote separately.
9. Re-run the targeted validation after merge/push.
10. Report any remote-specific push failure separately from local success.

## Validation examples
- `pytest` for the touched subsystem
- `py_compile` for edited Python modules
- Re-run the narrow smoke that exercises the changed runtime path

## Pitfalls
- A successful local merge does not imply all remotes accepted the push.
- A successful push does not imply the runtime is rebuilt or healthy.
- A runtime-pruning refactor should leave a concise incident note so the next session can reconstruct why the architecture changed.