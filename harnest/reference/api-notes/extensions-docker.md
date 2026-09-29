

## Sandbox configuration

| Option | Default | Purpose |
|---|---|---|
| `image` / `docker_path` | None | Select exactly one registry image or local Docker build context |
| `base_url` | Docker SDK default | Connect to an explicitly configured daemon |
| `network_policy` | `none()` | Grant no egress or supported unrestricted egress |
| `services` / `network` | Empty | Declare a private multi-container topology |
| `timeout_seconds` | 300 | Bound queueing, startup, and execution |
| `max_output_bytes` | 1 MiB | Bound captured output while streaming |
| `scope` | `EXECUTION` | Choose execution, invocation, or session reuse |
| `budget` | Harnest defaults | Bound CPU, memory, processes, and scratch space |
| `max_scopes` | 8 | Bound retained invocation or session identities |

## Public API and limits

| API | Role |
|---|---|
| `docker.sandbox(...)` / `docker_sandbox(...)` | Create a portable Docker-backed `Sandbox` |
| `docker.service(...)` | Declare one topology service |
| `docker.network(...)` | Declare the topology bridge and egress boundary |
| `docker.readiness(...)` | Declare a bounded service health command |
| `DockerScope` | Select execution, invocation, or session ownership |
| `DockerService`, `DockerNetwork`, `DockerReadiness` | Immutable topology contracts |
| `DockerSandboxProvider` | Runtime adapter implementing Harnest's sandbox provider contract |

A topology supports up to eight services. Each service allows 16 aliases, 32 declared ports, 64 environment entries, and 64 command arguments; bounded authored string values may use up to 8 KiB. Readiness permits 1 to 100 attempts with finite timing values. Service names and aliases must be unique portable lowercase DNS labels. These checks run before the Docker SDK receives configuration.

## Execution budgets

| Setting | Default and behavior |
|---|---|
| `scope` | `DockerScope.EXECUTION`: remove the topology after every call |
| `DockerScope.INVOCATION` | Reuse only for the same agent, user, session, and invocation |
| `DockerScope.SESSION` | Reuse only for the same agent, user, and session |
| `max_scopes` | `8`: evict the least recently used retained container before exceeding this cap |
| `budget.cpu` | `1.0` CPU, enforced by Docker |
| `budget.memory_bytes` | `512 MiB`, with no additional swap allowance |
| `budget.pids` | `64` processes |
| `budget.scratch_bytes` | `64 MiB` for writable `/tmp`; the root filesystem is read-only |
| `timeout_seconds` | `300`; includes queue waiting and active execution |
| `max_output_bytes` | `1 MiB` combined stdout/stderr, bounded while streaming |
| `network_policy` | `SandboxNetworkPolicy.none()`; uses Docker's `none` network without services or an internal topology bridge with services |
| `image` / `docker_path` | Supply exactly one; custom images must provide `python3` and must not declare volumes |
| `base_url` | Optional Docker daemon URL |

`options` retains the allowlisted parsing/retry fields only for callers explicitly constructing a native ADK adapter with `to_adk_executor()`. Those fields do not change Docker limits or add model tools to named sandbox assignments. Your authored tool decides whether to retry.
