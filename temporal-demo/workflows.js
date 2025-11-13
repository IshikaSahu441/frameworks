// workflows.js
export async function EchoWorkflow(message) {
  console.log('Workflow received:', message);
  return `Echo from Temporal: ${message}`;
}
