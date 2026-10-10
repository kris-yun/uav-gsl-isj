"""Expose the external recorder proxy only after all player services are ready."""
def expose_if_backends_ready(clients,creators):
 if not all(client.service_is_ready() for client in clients):return None
 return [create() for create in creators]
