

## Application loaders and storage

`load_compiled_application()` returns Harnest's compiled application record. `load_framework_app()` returns an exposed framework application object. Server embedding uses `session_store=` for portable storage or `framework_session_storage=` for a supported framework storage factory; lifecycle-owned storage cannot be combined with a second injected authority.
