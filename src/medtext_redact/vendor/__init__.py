"""Generic infrastructure helpers factored out of py-shared-tools and inlined
here directly, so this repo has no dependency on that separate (private)
repo and a fresh clone works fully offline.

Only the specific modules this project actually imports were copied:
``atomic_io``, ``config_loader``, ``logging_setup``, and ``tabular_io``
(``rest_adapter`` was copied too, and removed once the census surname list
was bundled instead of downloaded) -- each kept under its original module
and symbol names, so every call site needed only an import-path change,
not a rewrite. Anything
else py-shared-tools offers (remote_exec, script_export, sentinelone,
storage, generic retry-with-backoff) was never used here and wasn't copied.
"""
