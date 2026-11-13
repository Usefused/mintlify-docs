

## Framework construction

Managed agents accept model connectors directly. Advanced integrations use `model.build()` or `resolve_model(model)` during Harnest compilation or an active invocation to obtain the selected framework's model object. Custom `ModelConnector` subclasses implement `build(self)`.
