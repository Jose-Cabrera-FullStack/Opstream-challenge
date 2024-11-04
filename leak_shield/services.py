"""
This module defines the Manager class, which handles tasks from an SQS queue.

The Manager class is responsible for:
- Fetching messages from the SQS queue.
- Scheduling tasks based on the messages received.

Example usage:
    async def example_task(arg1, arg2):
        print(f"Task executed with arguments: {arg1}, {arg2}")

    tasks = {
        'example_task': example_task,
    }

    manager = Manager(queue_name='example_queue', tasks=tasks)
    asyncio.run(manager.main())
"""

import json
import asyncio
import boto3

from leak_shield.adapters import LeakScannerAdapter


class Manager:
    """
    Manager class to handle tasks from an SQS queue.

    Attributes:
        queue (str): The name of the SQS queue.
        tasks (dict): A dictionary mapping task names to coroutine functions.
        loop (asyncio.AbstractEventLoop): The event loop for running asynchronous tasks.

    Methods:
        _get_messages(): Asynchronously reads and pops messages from the SQS queue.
        main(): Main loop that continuously fetches messages from the queue and schedules tasks.
    """

    def __init__(self, queue_name: str, tasks: dict):
        self.loop = asyncio.get_event_loop()
        self.queue = queue_name
        self.tasks = tasks

    async def _get_messages(self):
        """Read and pop messages from SQS queue"""
        raise NotImplementedError

    async def main(self):
        """For a given task:
        >>> async def say(something):
        pass
        Messages from queue are expected to have the format:
        >>> message = dict(task='say', args=('something',), kwargs={})
        >>> message = dict(task='say', args=(), kwargs={'something': 'something else'})
        """
        while True:
            messages = await self._get_messages()
            for message in messages:
                body = json.loads(message['Body'])
                task_name = body.get('task')
                args = body.get('args', ())
                kwargs = body.get('kwargs', {})
                task = self.tasks.get(task_name)
                self.loop.create_task(task(*args, **kwargs))
            await asyncio.sleep(1)


class LeakDetectionManager(Manager):
    """
    A specialized Manager class for handling leak detection tasks from an SQS queue.

    This class extends the Manager class to specifically handle leak detection operations.
    It automatically configures task mappings for file and message scanning using LeakScanner
    and sets up the AWS SQS client connection.

    Attributes:
        queue_name (str): The name of the SQS queue to monitor
        sqs: Boto3 SQS client instance
        queue_url (str): The URL of the SQS queue
        tasks (dict): Predefined mapping of task names to LeakScanner methods

    Methods:
        _get_messages(): Implements the abstract method to fetch and delete messages from SQS
    """

    def __init__(self, queue_name: str, region_name: str = "us-east-1"):
        tasks = {
            'scan_file': LeakScannerAdapter.scan_file,
            'scan_message': LeakScannerAdapter.scan_message
        }
        super().__init__(queue_name, tasks)
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.queue_url = self.sqs.get_queue_url(
            QueueName=queue_name)['QueueUrl']

    async def _get_messages(self):
        """Read and pop messages from SQS queue and process them"""
        response = self.sqs.receive_message(
            QueueUrl=self.queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20
        )
        messages = response.get('Messages', [])

        for message in messages:
            try:
                body = json.loads(message['Body'])
                task_name = body.get('task')

                if task_name == 'scan_message':
                    channel_id = body.get('channel_id')
                    user_id = body.get('user_id')
                    content = body.get('content')

                    if all([channel_id, user_id, content]):
                        await LeakScannerAdapter.scan_message(channel_id, user_id, content)

                elif task_name == 'scan_file':
                    file_path = body.get('file_path')
                    if file_path:
                        await LeakScannerAdapter.scan_file(file_path)

            except (json.JSONDecodeError, KeyError) as e:
                # TODO: Log error properly
                print(f"Error processing message: {e}")
            finally:
                self.sqs.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )

        return messages
