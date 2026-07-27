// Compile-checks an MDX document from stdin using the real MDX compiler.
// Prints {"ok": true} or {"ok": false, "error": "..."} as JSON on stdout.
// Invoked by server/agent/nodes/mdx_validator.py with cwd=client/ so that
// @mdx-js/mdx resolves from client/node_modules.
import { compile } from "@mdx-js/mdx";

let source = "";
process.stdin.setEncoding("utf8");
for await (const chunk of process.stdin) source += chunk;

try {
  await compile(source, { format: "mdx" });
  process.stdout.write(JSON.stringify({ ok: true }));
} catch (err) {
  const message = err && err.message ? String(err.message) : String(err);
  const line = err && err.line ? ` (line ${err.line})` : "";
  process.stdout.write(JSON.stringify({ ok: false, error: message + line }));
}
