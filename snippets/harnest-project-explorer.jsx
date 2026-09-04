export const HarnestProjectExplorer = () => {
  // Pair every path with its requirement and preview to keep selection consistent.
  const entries = [
  {
    "label": "agent.py",
    "path": "agent.py",
    "description": "The root agent. Managed ADK and LangGraph projects share this declaration; config.yaml selects the framework.",
    "code": "from harnest.agent import Agent\nfrom harnest.model import LiteLLMModel\n\n\nroot_agent = Agent(\n    name=\"support_agent\",\n    history=\"session\",\n    model=LiteLLMModel.from_openai_environment(),\n)",
    "language": "python",
    "optional": false,
    "href": "/harnest/build/agents-and-graphs",
    "example": false
  },
  {
    "label": "instructions.md",
    "path": "instructions.md",
    "description": "The root agent’s instructions. Harnest loads this file for the managed agent.",
    "code": "You are Support Agent.\n\nAnswer clearly, acknowledge uncertainty, and use discovered tools when they are relevant.",
    "language": "markdown",
    "optional": false,
    "href": "/harnest/build/project-configuration",
    "example": false
  },
  {
    "label": "config.yaml",
    "path": "config.yaml",
    "description": "Agent, framework, and deployment settings. Add an optional root server section to override local serving defaults. This preview uses ADK; select langgraph for a managed LangGraph project.",
    "code": "apiVersion: harnest.dev/v1alpha1\nkind: Agent\nmetadata:\n  name: support-agent\n  displayName: Support Agent\nspec:\n  enabled: true\n  entrypoint: agent:root_agent\n  framework:\n    name: adk\n    mode: managed\n  runtime:\n    version: \"3.12\"\n    dependencyFile: pyproject.toml\n  resources:\n    cpu: \"1\"\n    memory: 1Gi\n    ephemeralStorage: 1Gi\n    timeoutSeconds: 300\n    maxConcurrentRequests: 8\n  scaling:\n    minReplicas: 0\n    maxReplicas: 1\n  # Supply OPENAI_API_KEY through the command environment or deployment secrets.\n  environment:\n    OPENAI_MODEL: gpt-4.1-mini\n    OPENAI_BASE_URL: https://api.openai.com/v1\n    OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT: NO_CONTENT\n    ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS: \"false\"",
    "language": "yaml",
    "optional": false,
    "href": "/harnest/build/project-configuration",
    "example": false
  },
  {
    "label": "agent-card.yaml",
    "path": "agent-card.yaml",
    "description": "Public identity, capabilities, and the A2A interfaces the agent advertises.",
    "code": "name: Support Agent\ndescription: A self-contained Harnest agent.\nversion: 0.1.0\nsupportedInterfaces:\n  - url: http://127.0.0.1:8080\n    protocolBinding: HTTP+JSON\n    protocolVersion: \"1.0\"\ncapabilities:\n  streaming: true\ndefaultInputModes:\n  - text/plain\ndefaultOutputModes:\n  - text/plain\nskills:\n  - id: respond\n    name: Respond\n    description: Responds clearly to user requests.\n    tags: [assistant]",
    "language": "yaml",
    "optional": false,
    "href": "/harnest/runtime/a2a/serve",
    "example": false
  },
  {
    "label": "pyproject.toml",
    "path": "pyproject.toml",
    "description": "Your Python dependencies. Harnest supplies the framework; environment sync generates uv.lock.",
    "code": "[project]\nname = \"support-agent\"\nversion = \"0.1.0\"\nrequires-python = \">=3.12,<3.13\"\ndependencies = []\n\n[dependency-groups]\ndev = [\"pytest>=8,<9\"]\n\n[tool.uv]\npackage = false",
    "language": "toml",
    "optional": false,
    "href": "/harnest/build/project-configuration",
    "example": false
  },
  {
    "label": "harnest.lock",
    "path": "harnest.lock",
    "description": "The project schema and resolved framework version. Environment sync adds the exact framework pin. Commit this file; schema upgrades preserve that pin.",
    "code": "apiVersion: harnest.dev/v1alpha1\nkind: ProjectLock\nprojectSchema: 3",
    "language": "yaml",
    "optional": false,
    "href": "/harnest/build/project-configuration",
    "example": false
  },
  {
    "label": "lib/",
    "path": "lib/messages.py",
    "description": "Optional shared Python helpers. Omit this folder until you need reusable code. Import this example with from harnest.lib.messages import normalize.",
    "code": "def normalize(message: str) -> str:\n    \"\"\"Collapse whitespace in a message.\"\"\"\n    return \" \".join(message.split())",
    "language": "python",
    "optional": true,
    "href": "/harnest/build/data-models-and-shared-libraries",
    "example": true
  },
  {
    "label": "models/",
    "path": "models/messages.py",
    "description": "Optional Pydantic contracts. Import this example with from harnest.models.messages import Message.",
    "code": "from pydantic import BaseModel, Field\n\n\nclass Message(BaseModel):\n    \"\"\"Validate a non-empty message.\"\"\"\n\n    text: str = Field(min_length=1)",
    "language": "python",
    "optional": true,
    "href": "/harnest/build/data-models-and-shared-libraries",
    "example": true
  },
  {
    "label": "tools/",
    "path": "tools/echo.py",
    "description": "Optional Agent Tools. Add one public callable per file; its name must match the filename.",
    "code": "from harnest.tool import tool\n\n\n@tool\ndef echo(message: str) -> str:\n    \"\"\"Return a message unchanged.\"\"\"\n    return message",
    "language": "python",
    "optional": true,
    "href": "/harnest/build/agent-tools",
    "example": true
  },
  {
    "label": "tasks/",
    "path": "tasks/prepare_report.py",
    "description": "Optional queued work. Direct calls run inline; deferred execution needs task storage. Tasks are not automatically exposed as Agent Tools.",
    "code": "from harnest.task import task\n\n\n@task(queue=\"reports\", max_retries=3)\nasync def prepare_report(subject: str) -> dict[str, str]:\n    \"\"\"Prepare a report result without external side effects.\"\"\"\n    return {\"subject\": subject, \"status\": \"ready\"}",
    "language": "python",
    "optional": true,
    "href": "/harnest/build/queued-tasks",
    "example": true
  },
  {
    "label": "cron/",
    "path": "cron/daily_report.py",
    "description": "Optional UTC schedules. This example also needs tasks/prepare_report.py and the task runtime and store.",
    "code": "from harnest.cron import Cron\nfrom tasks.prepare_report import prepare_report\n\n\n# Use UTC so the schedule does not depend on the host timezone.\ndaily_report = Cron(\n    \"0 9 * * 1-5\",\n    task=prepare_report,\n    arguments={\"subject\": \"daily\"},\n)",
    "language": "python",
    "optional": true,
    "href": "/harnest/build/scheduled-tasks",
    "example": true
  },
  {
    "label": "subagents/",
    "path": "subagents/helper.py",
    "description": "Optional SubAgents. Reference this flat helper explicitly in your root Graph; use a folder for a SubAgent with its own resources.",
    "code": "from harnest.agent import Agent\nfrom harnest.model import LiteLLMModel\n\n\nhelper = Agent(\n    name=\"helper\",\n    model=LiteLLMModel.from_openai_environment(),\n    instruction=\"Summarize the request and acknowledge missing information.\",\n)",
    "language": "python",
    "optional": true,
    "href": "/harnest/build/subagents",
    "example": true
  },
  {
    "label": "mcp/",
    "path": "mcp/knowledge.py",
    "description": "Optional MCP Client connections. Export a client() factory and configure the endpoint in your environment.",
    "code": "import os\n\nfrom harnest.mcp import MCPClient\n\n\ndef client():\n    \"\"\"Read the endpoint when Harnest discovers this client.\"\"\"\n    return MCPClient.streamable_http(\n        os.environ[\"HARNEST_MCP_URL\"],\n        prefix=\"knowledge\",\n    )",
    "language": "python",
    "optional": true,
    "href": "/harnest/build/mcp-client",
    "example": true
  },
  {
    "label": "lifecycle/",
    "path": "lifecycle/storage.py",
    "description": "Included and active: the generated agent uses this provider for session and checkpoint storage. Keep it unless you replace those bindings. Additional lifecycle hooks and factories are optional.",
    "code": "from harnest.lifecycle import lifecycle\nfrom harnest.store import MemoryStore\n\n\n@lifecycle.storage.sessions\n@lifecycle.storage.checkpoints\ndef state_store():\n    \"\"\"Share one lifecycle-owned store without placing it in lib.\"\"\"\n    return MemoryStore()",
    "language": "python",
    "optional": false,
    "href": "/harnest/runtime/checkpoints-and-storage",
    "example": false
  },
  {
    "label": "extensions/",
    "path": "extensions/starter_runtime/extension.yaml",
    "description": "Optional Harnest Extensions package reusable application functionality. Declare extension.yaml, export the singleton from extension.py, and put package-owned hooks in lifecycle/. Agent Plugins live separately in plugins/.",
    "code": "apiVersion: harnest.dev/v1alpha1\nkind: Extension\nmetadata:\n  name: starter_runtime\n  version: 0.1.0\nruntime:\n  entrypoint: extension:extension\ncapabilities: []",
    "language": "yaml",
    "optional": true,
    "href": "/harnest/build/extensions/create",
    "example": true
  },
  {
    "label": "plugins/",
    "path": "plugins/warehouse/plugin.json",
    "description": "Agent Plugins 1.0 packages contain plugin.json and optional skills/ and mcp.json components. Harnest discovers them without Python registration. Application lifecycle behavior belongs in lifecycle/ or a Harnest Extension.",
    "code": "{\n  \"$schema\": \"https://agent-plugins.org/schemas/1.0.0/plugin.schema.json\",\n  \"name\": \"warehouse\",\n  \"version\": \"1.0.0\",\n  \"description\": \"Query the shared warehouse\"\n}",
    "language": "json",
    "optional": true,
    "href": "/harnest/build/agent-plugins",
    "example": true
  },
  {
    "label": "sandbox/",
    "path": "sandbox/calculations.py",
    "description": "Optional execution environments. Assign sandboxes=[\"calculations\"] on an Agent, then call context.sandboxes[\"calculations\"] from an authored tool. This container needs Docker when executed.",
    "code": "from harnest.sandbox import Sandbox\n\n\ncalculations = Sandbox.container(\n    image=\"python:3.12-slim\",\n    network=False,\n    timeout_seconds=120,\n    max_output_bytes=1_048_576,\n)",
    "language": "python",
    "optional": true,
    "href": "/harnest/build/sandboxing",
    "example": true
  },
  {
    "label": "skills/",
    "path": "skills/getting-started/SKILL.md",
    "description": "Optional Agent Skills. Each skill lives in its own directory with a SKILL.md instruction file.",
    "code": "---\nname: getting-started\ndescription: Apply the agent's core instructions when answering a general request that does not require a more specialized skill.\n---\n\n# Getting started\n\n1. Identify the user's requested outcome before acting.\n2. Use a discovered tool only when it materially helps produce that outcome.\n3. State uncertainty plainly and never invent tool results or external facts.\n4. Return a concise answer with the most useful result first.",
    "language": "markdown",
    "optional": true,
    "href": "/harnest/build/agent-skills",
    "example": true
  },
  {
    "label": "evals/",
    "path": "evals/starter.evalset.json",
    "description": "Optional evaluation datasets. Add these when you want to check agent responses against expected outcomes.",
    "code": "{\n  \"eval_set_id\": \"starter\",\n  \"name\": \"Starter evaluation\",\n  \"eval_cases\": [\n    {\n      \"evalId\": \"answers_greeting\",\n      \"conversation\": [\n        {\n          \"userContent\": {\"role\": \"user\", \"parts\": [{\"text\": \"Say hello briefly.\"}]},\n          \"finalResponse\": {\"role\": \"model\", \"parts\": [{\"text\": \"Hello!\"}]}\n        }\n      ],\n      \"sessionInput\": {\"appName\": \"support_agent\", \"userId\": \"eval-user\", \"state\": {}}\n    }\n  ]\n}",
    "language": "json",
    "optional": true,
    "href": "/harnest/build/evaluations",
    "example": true
  },
  {
    "label": "tests/",
    "path": "tests/unit/test_agent.py",
    "description": "Optional authored tests. Put offline checks in tests/unit/ and opt-in live checks in tests/smoke/. The default scaffold creates a guide in each folder.",
    "code": "def test_agent_name(agent):\n    \"\"\"Check the generated agent’s public name without a model call.\"\"\"\n    assert agent.name == \"support_agent\"",
    "language": "python",
    "optional": true,
    "href": "/harnest/build/testing-and-compilation",
    "example": true
  }
];
  const [selectedIndex, setSelectedIndex] = useState(0);
  const selected = entries[selectedIndex];
  // Native buttons keep every path reachable with Tab, Enter, and Space.
  const selectEntry = (event) => {
    setSelectedIndex(Number(event.currentTarget.value));
  };
  return (
    <div className="harnest-explorer not-prose">
      <style>{`
        .harnest-explorer { border: 1px solid #8883; border-radius: 12px; overflow: hidden; display: grid; grid-template-columns: 210px minmax(0, 1fr); margin: 24px 0; font-size: 13px; }
        .harnest-explorer-nav { border-right: 1px solid #8883; min-width: 0; }
        .harnest-explorer-heading { padding: 14px 16px; border-bottom: 1px solid #8883; font-weight: 500; min-height: 49px; }
        .harnest-explorer-paths { padding: 8px; max-height: 520px; overflow-y: auto; }
        .harnest-explorer-path { display: flex; align-items: center; justify-content: space-between; gap: 8px; width: 100%; padding: 9px 10px; border: 0; border-radius: 6px; background: transparent; color: inherit; text-align: left; cursor: pointer; font: inherit; }
        .harnest-explorer-path:hover { background: #8881; }
        .harnest-explorer-path[aria-pressed="true"] { background: #8882; font-weight: 600; }
        .harnest-explorer-path:focus-visible, .harnest-explorer a:focus-visible { outline: 2px solid currentColor; outline-offset: -2px; }
        .harnest-explorer-tag { font: 10px ui-monospace, monospace; font-weight: 400; opacity: .65; }
        .harnest-explorer-preview { min-width: 0; height: 0; min-height: 100%; display: flex; flex-direction: column; }
        .harnest-explorer-description { padding: 14px 16px; border-bottom: 1px solid #8883; line-height: 1.65; }
        .harnest-explorer-description p { margin: 0 0 8px; }
        .harnest-explorer-description a { color: inherit; text-decoration: underline; text-underline-offset: 3px; }
        .harnest-explorer-example { font-size: 12px; opacity: .65; }
        /* Let the folder list set the desktop height; long code scrolls within the remaining space. */
        .harnest-explorer-code { height: 0; min-height: 0; flex: 1; overflow: auto; }
        .harnest-explorer-code > .code-block { margin: 0; min-height: 100%; border: 0; border-radius: 0; }
        .harnest-explorer-code [data-component-part="code-block-root"] { border-radius: 0; }
        @media (max-width: 640px) {
          .harnest-explorer { grid-template-columns: minmax(0, 1fr); }
          .harnest-explorer-nav { border-right: 0; border-bottom: 1px solid #8883; }
          .harnest-explorer-paths { max-height: 190px; }
          /* Stacked panels need their own code height once there is no adjacent folder column. */
          .harnest-explorer-preview { height: auto; min-height: 0; }
          .harnest-explorer-code { height: auto; flex: none; max-height: 400px; }
        }
      `}</style>
      <div className="harnest-explorer-nav">
        <div className="harnest-explorer-heading">support-agent/</div>
        <nav className="harnest-explorer-paths" aria-label="Generated project files and folders">
          {/* Only guide-only folders are optional; storage remains active in this scaffold. */}
          {entries.map((entry, index) => (
            <button key={entry.label} type="button" className="harnest-explorer-path" value={index} aria-pressed={index === selectedIndex} aria-controls="harnest-file-preview" onClick={selectEntry}>
              <span>{entry.label}</span>
              {entry.optional && <span className="harnest-explorer-tag">optional</span>}
            </button>
          ))}
        </nav>
      </div>
      <section id="harnest-file-preview" className="harnest-explorer-preview" aria-label="Selected file preview" aria-live="polite" aria-atomic="true">
        <div className="harnest-explorer-heading">{selected.path}</div>
        <div className="harnest-explorer-description">
          <p>{selected.description}</p>
          {/* Label illustrative files so readers do not mistake them for generated files. */}
          {selected.example && <p className="harnest-explorer-example">Example · this folder contains only _README.md guides by default.</p>}
          <a href={selected.href}>Read the guide →</a>
        </div>
        <div className="harnest-explorer-code">
          <CodeBlock key={selected.path} language={selected.language} lines>{selected.code}</CodeBlock>
        </div>
      </section>
    </div>
  );
};
