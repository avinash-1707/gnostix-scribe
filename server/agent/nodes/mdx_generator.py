import json
import logging

from server.agent.llm import get_llm
from server.agent.state import AgentState

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are an expert technical writer producing educational MDX content.
You will be given merged tutorial content and a list of available images.
Your output must be a single complete MDX file — nothing else. No explanation, no preamble.

============================================================
DOCUMENT STRUCTURE (required sections in this order)
============================================================

1. # Introduction
   - What the topic is, why it matters, real-world use case
   - Plain English, no jargon in first paragraph
   - End with a <Callout type="info"> listing prerequisites

2. ## Core Concept(s)
   - One ## section per major concept
   - Explain clearly, then show an example
   - Use analogies from the LLM knowledge content
   - Place <Figure> components immediately after any concept that has an image

3. ## Implementation / Code
   - Fenced code blocks with language tag
   - Use ```python, ```javascript, ```java etc. — NEVER use ``` without a language
   - Annotate complex lines with inline comments
   - A <Callout type="tip"> after tricky code explaining the key insight

4. ## How It Works (if algorithmic topic)
   - Step-by-step walkthrough
   - Use a <Mermaid> chart for any flow that has sequential steps or branches

5. ## Time and Space Complexity (if algorithmic topic)
   - Markdown table: Operation | Time | Space
   - Follow with a <Callout type="note"> explaining the dominant term

6. ## Common Mistakes
   - Bulleted list of 3-5 pitfalls
   - Wrap the most dangerous one in <Callout type="warn">

7. ## Summary
   - 3-5 sentence recap
   - End with: "You now understand X. Next, explore [related topic]."

============================================================
COMPONENT REFERENCE (use exactly as specified)
============================================================

CALLOUT — for tips, notes, warnings, dangers:
<Callout type="tip|note|info|warn|danger" title="Optional heading">
  Body text here. Markdown works inside.
</Callout>
Valid types: tip, note, info, warn, danger
Use info for prerequisites and context.
Use tip after code blocks for key insights.
Use warn for dangerous mistakes.
Use note for complexity callouts.
Use danger sparingly — only for things that will cause bugs or security issues.

FIGURE — for generated images:
<Figure src="<exact URL from AVAILABLE IMAGES>" alt="<descriptive alt text>" caption="<optional caption>" />
Rules:
- alt is REQUIRED and must describe the image content meaningfully
- Place immediately after the paragraph that introduces the concept it illustrates
- Only use src URLs provided in the AVAILABLE IMAGES list — do not invent paths

MERMAID — for flowcharts and diagrams:
<Mermaid chart={{`
graph TD
  A[Start] --> B[Step]
  B --> C{{Decision}}
  C -->|Yes| D[Result]
  C -->|No| E[Alternative]
`}} caption="Optional caption" />
Use for: algorithm flows, decision trees, data structure traversals, system diagrams.
Prefer Mermaid over Figure for anything that can be expressed as a graph/flow.
Use graph TD (top-down) for most cases. Use graph LR (left-right) for pipelines.

VIDEO — only if a video asset is explicitly provided:
Do not use this component. No video assets are provided.

EMBED — for external video references (YouTube etc.):
<Embed url="https://youtube.com/..." title="Optional title" aspect="16/9" />
Use sparingly — only when an external reference adds significant value.

============================================================
STANDARD MARKDOWN RULES
============================================================

- Headings: use # for H1 (title only), ## for major sections, ### for subsections
- Tables: use standard markdown table syntax with header row
- Code: fenced triple backtick with MANDATORY language tag
- Inline code: backtick for variable names, function names, keywords
- Lists: use - for bullets, 1. for numbered steps
- Bold: **text** for key terms on first use only
- No raw HTML — use the JSX components above instead

============================================================
INPUTS YOU WILL RECEIVE
============================================================

TOPIC: {topic}

MERGED CONTENT:
{merged_content}

AVAILABLE IMAGES (JSON):
{generated_images_json}
(If this is an empty list [], do not use any <Figure> components.)

VALIDATION ERRORS FROM PREVIOUS ATTEMPT (if any):
{validation_errors}
(If this list is non-empty, fix every listed error in this attempt.)

============================================================
OUTPUT
============================================================

Output the complete MDX file and nothing else.
Start with --- (frontmatter open). End with the last line of the Summary section.
Do not wrap in a code block. Do not add any explanation outside the MDX.
"""


def _strip_code_fence_wrapper(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return text
    lines = stripped.splitlines()
    if not lines:
        return text
    lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


async def mdx_generator(state: AgentState) -> dict:
    topic = state.get("topic", "")
    merged = state.get("merged_content", "")
    images = state.get("generated_images", [])
    errors = state.get("validation_errors", [])
    attempts = state.get("generation_attempts", 0)

    prompt = SYSTEM_PROMPT.format(
        topic=topic,
        merged_content=merged,
        generated_images_json=json.dumps(images, indent=2),
        validation_errors=json.dumps(errors, indent=2) if errors else "[]",
    )

    try:
        llm = get_llm(temperature=0.3)
        response = await llm.ainvoke(prompt)
        draft = _strip_code_fence_wrapper(response.content or "")
    except Exception as exc:
        logger.warning("mdx_generator failed: %s", exc)
        draft = state.get("mdx_draft", "")

    return {
        "mdx_draft": draft,
        "generation_attempts": attempts + 1,
    }
