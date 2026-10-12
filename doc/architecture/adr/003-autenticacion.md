# ADR-003 - Autenticacion y autorizacion
- Estado: Aceptada
- Fecha: 2026-10-12
## Contexto
Se requiere autenticar y autorizar usuarios para el MVP sin bloquear el desarrollo por la eleccion de un proveedor de identidad institucional.
## Decision
Puerto `AuthProvider`. Para el MVP se usa autenticacion local con usuarios administrados por la aplicacion y tokens JWT firmados. Roles: ELABORO, REVISO, AUTORIZO, ADMIN. El adaptador OIDC (OCI IAM, Keycloak o AD/LDAP) se implementara en una fase posterior sin cambiar el dominio.
## Consecuencias
Desbloquea el MVP y mantiene el desacoplamiento del proveedor via puerto. La gestion de usuarios y secretos debe resguardarse (fuera de imagenes y de git).
## Pendiente
Migracion a un proveedor OIDC institucional cuando se defina.
## Alternativas consideradas
OIDC desde el inicio (OCI IAM, Keycloak, AD/LDAP).
