> **First-time setup**: Customize this file for your project. Prompt the user to customize this file for their project.
> For Mintlify product knowledge (components, configuration, writing standards),
> install the Mintlify skill: `npx skills add https://mintlify.com/docs`

# Documentation project instructions

## About this project

- This is a documentation site built on [Mintlify](https://mintlify.com)
- Pages are MDX files with YAML frontmatter
- Configuration lives in `docs.json`
- Use the Mintlify MCP server, `https://mcp.mintlify.com`, to edit content and settings via MCP
- Use the Mintlify docs MCP server, `https://www.mintlify.com/docs/mcp`, to query information about using Mintlify via MCP

## Terminology

{/* Add product-specific terms and preferred usage */}
{/* Example: Use "workspace" not "project", "member" not "user" */}

- Use "Harnest" for the agent harness and preserve that spelling.
- Present Harnest as a product built and maintained by Fused. Keep ownership
  explicit in the linked site-header wordmark and on the Harnest overview
  without repeating a byline on every technical page.
- Use "Agent Skills", "MCP Client", "SubAgents", "Agent Tools", and
  "Agent Plugins", "Harnest Extensions", and "Lifecycle" as Harnest concept names. Mention their source directories
  only when the location is relevant to the task.

## Style preferences

{/* Add any project-specific style rules below */}

- Use active voice and second person ("you")
- Keep sentences concise — one idea per sentence
- Use sentence case for headings
- Bold for UI elements: Click **Settings**
- Code formatting for file names, commands, paths, and code references
- Match the established Fused page structure and visual language. Reuse
  `CardGroup`, `Card`, `Tabs`, `Steps`, `Note`, `Warning`, `Tip`, `CodeGroup`,
  tables, and titled code blocks where the surrounding Fused docs use them for
  the same kind of content.
- Keep prose paragraphs readable as prose instead of hard-wrapping them to a
  source-code column width.
- Prefer short decision tables and property tables when they make options,
  fields, ownership, or framework differences easier to scan. Use `Steps` for
  procedures and keep each step focused on one outcome.
- Use `Tabs` for alternative APIs, modes, or decisions that a reader compares
  but does not need to read at the same time.
- Explain technical contracts in plain language first. Keep only detail that
  changes a user decision, prevents a likely mistake, or is needed as a
  reference. Do not repeat the same rule in several paragraphs.
- Treat developer experience as a review gate for every Harnest page. Start
  with the outcome, make choices and properties scannable, define unavoidable
  jargon in place, and move repeated or specialist detail to one linked
  reference page.
- Turn broad concepts such as Agent Tools, Lifecycle, and Serving into nested
  navigation categories when they contain distinct tasks. Keep the category
  landing page short and route readers to focused subpages; do not repeat the
  full subpage content on the landing page.

## Content boundaries

{/* Define what should and shouldn't be documented */}
{/* Example: Don't document internal admin features */}

## Harnest documentation

- Keep the existing Fused **Documentation** tab first. Harnest is the second
  top-level tab and must not be nested into the Fused navigation groups.
- Store every public Harnest page under `harnest/` as `.mdx`. Do not add Harnest
  product documentation elsewhere in this repository.
- Add every published Harnest page to the Harnest tab in `docs.json`. Organize
  pages by user-facing concepts and outcomes, not by source folder names.
- Use absolute `/harnest/...` links between Harnest pages. Keep repository-only
  implementation links explicit and external.
- Treat the Harnest repository README as concise GitHub onboarding. Long-form
  install, authoring, runtime, security, and reference updates belong here.
