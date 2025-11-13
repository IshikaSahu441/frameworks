// client.js
import { Connection, Client } from '@temporalio/client';

async function run() {
  const connection = await Connection.connect({ address: 'localhost:7233' });

  const client = new Client({
    connection,
    namespace: 'default',
  });

  const handle = await client.workflow.start('EchoWorkflow', {
    args: ['Hello Temporal!'],
    taskQueue: 'hello-world',
    workflowId: 'hello-workflow-' + Date.now(),
  });

  console.log(`🚀 Started workflow ${handle.workflowId}`);
  console.log('Waiting for result...');

  const result = await handle.result();
  console.log('✅ Workflow result:', result);
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
