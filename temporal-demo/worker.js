// worker.js
import { Worker } from '@temporalio/worker';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function run() {
  const worker = await Worker.create({
    workflowsPath: path.join(__dirname, 'workflows.js'),
    taskQueue: 'hello-world',
  });

  console.log('✅ Worker started and listening for workflows...');
  await worker.run();
}

run().catch((err) => {
  console.error('❌ Worker failed:', err);
  process.exit(1);
});
